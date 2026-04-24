<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import http from '../utils/http'
import { uploadLeaveFiles } from '../api'

interface Props {
  show: boolean
  type: 'leave' | 'student' | 'reviewer' | 'teacher' | 'course'
  onClose: () => void
  onSuccess: () => void
  itemLabel?: string
  // 编辑模式
  editId?: number | null
  editData?: any
}

const props = withDefaults(defineProps<Props>(), {
  itemLabel: '',
  editId: null,
  editData: null
})

// Current user role
const currentUserRole = computed(() => localStorage.getItem('role'))


// Modal state
const isSubmitting = ref(false)
const error = ref('')
const success = ref('')

// File upload state
const file = ref<File | null>(null)
const isUploading = ref(false)
const proofFiles = ref<File[]>([])
const proofUploading = ref(false)
const uploadedFilePaths = ref<string[]>([])

// Options for select fields
const reviewers = ref<any[]>([])
const teachers = ref<any[]>([])
const courses = ref<any[]>([])
const schools = ref<any[]>([])
const roles = ref<any[]>([])
const loadingOptions = ref(false)

// Get options data
const fetchOptions = async () => {
  loadingOptions.value = true
  try {
    if (props.type === 'student') {
      const [reviewersRes, schoolsRes, nextIdRes] = await Promise.all([
        http.get('/reviewers', { params: { page_size: 100, school_id: formData.value.school_id || undefined } }),
        http.get('/schools', { params: { page_size: 100 } }),
        http.get('/students/next-id')
      ])
      reviewers.value = (reviewersRes as any).items || []
      schools.value = (schoolsRes as any).items || []
      formData.value.student_id = String((nextIdRes as any).next_id || '')
    } else if (props.type === 'reviewer') {
      const [schoolsRes, rolesRes, nextIdRes] = await Promise.all([
        http.get('/schools', { params: { page_size: 100 } }),
        http.get('/roles', { params: { page_size: 100 } }),
        http.get('/reviewers/next-id')
      ])
      schools.value = (schoolsRes as any).items || []
      roles.value = (rolesRes as any).items || []
      formData.value.reviewer_id = String((nextIdRes as any).next_id || '')
    } else if (props.type === 'teacher') {
      const [response, nextIdRes] = await Promise.all([
        http.get('/teachers'),
        http.get('/teachers/next-id')
      ])
      teachers.value = (response as any).items || []
      formData.value.teacher_id = String((nextIdRes as any).next_id || '')
    } else if (props.type === 'course') {
      const [response, nextIdRes] = await Promise.all([
        http.get('/teachers'),
        http.get('/courses/next-id')
      ])
      teachers.value = (response as any).items || []
      formData.value.course_id = String((nextIdRes as any).next_id || '')
    } else if (props.type === 'leave') {
      const response = await http.get('/courses')
      courses.value = (response as any).items || []
    }
  } catch (error) {
    console.error('获取选项数据失败:', error)
  } finally {
    loadingOptions.value = false
  }
}

// Close modal
const closeModal = () => {
  resetForm()
  props.onClose()
}

// Reset form
const resetForm = () => {
  error.value = ''
  success.value = ''
  isSubmitting.value = false
  isUploading.value = false
  file.value = null
  proofFiles.value = []
  proofUploading.value = false
  uploadedFilePaths.value = []

  // Reset form data
  formData.value = getDefaultFormData()
}

// Get default form data based on type
const getDefaultFormData = () => {
  switch (props.type) {
    case 'leave':
      return {
        student_id: null,
        guarantee_student_id: null,
        course_id: 0,
        leave_date: '',
        leave_hours: null,
        leave_type: '',
        remarks: ''
      }
    case 'student':
      return {
        student_id: '',
        student_name: '',
        school_id: '',
        reviewer_id: '',
        password: '',
        guarantee_permission: ''
      }
    case 'reviewer':
      return {
        reviewer_id: '',
        reviewer_name: '',
        school_id: '',
        role_id: '',
        password: ''
      }
    case 'teacher':
      return {
        teacher_id: '',
        name: '',
        password: ''
      }
    case 'course':
      return {
        course_id: '',
        course_name: '',
        teacher_id: '',
        class_hours: ''
      }
    default:
      return {}
  }
}

// Form data
const formData = ref<any>(getDefaultFormData())

// Helper: safely parse int from form data
const toInt = (v: any): number | null => {
  const n = parseInt(String(v ?? ''))
  return isNaN(n) ? null : n
}


// Handle proof file change for leave (multiple files)
const handleProofFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    // Add new files to existing selection
    for (let i = 0; i < target.files.length; i++) {
      proofFiles.value.push(target.files[i])
    }
  }
  // Reset the input so the same file can be selected again if needed
  target.value = ''
}

// Remove a file from selection
const removeProofFile = (index: number) => {
  proofFiles.value.splice(index, 1)
}

// Clear all selected files
const clearProofFiles = () => {
  proofFiles.value = []
  uploadedFilePaths.value = []
}


// Handle create / edit
const handleCreate = async () => {
  try {
    isSubmitting.value = true
    error.value = ''
    success.value = ''

    const isEditMode = props.editId != null
    let endpoint = ''
    let payload: any = {}

    switch (props.type) {
      case 'leave':
        if (isEditMode) {
          endpoint = `/leaves/edit/${props.editId}`
          payload = {
            course_id: formData.value.course_id === 0 ? null : formData.value.course_id,
            leave_date: formData.value.leave_date,
            leave_hours: formData.value.leave_hours ? formData.value.leave_hours.toString() : null,
            leave_type: formData.value.leave_type || null,
            remarks: formData.value.remarks || null,
          }
        } else {
          endpoint = '/leaves'
          // 先创建请假条（不包含materials），得到leave_id后再上传文件
          payload = {
            student_id: toInt(formData.value.student_id),
            guarantee_student_id: formData.value.guarantee_student_id || null,
            course_id: formData.value.course_id === 0 ? null : formData.value.course_id,
            leave_date: formData.value.leave_date,
            leave_hours: formData.value.leave_hours ? formData.value.leave_hours.toString() : null,
            status: '待审批',
            leave_type: formData.value.leave_type || null,
            remarks: formData.value.remarks || null,
            materials: null
          }
        }
        break
      case 'student':
        endpoint = '/students'
        payload = {
          student_id: toInt(formData.value.student_id) || 0,
          student_name: formData.value.student_name,
          school_id: toInt(formData.value.school_id),
          reviewer_id: toInt(formData.value.reviewer_id),
          password: formData.value.password || null,
          guarantee_permission: formData.value.guarantee_permission || null
        }
        break
      case 'reviewer':
        endpoint = '/reviewers'
        payload = {
          reviewer_id: toInt(formData.value.reviewer_id) || 0,
          reviewer_name: formData.value.reviewer_name,
          school_id: toInt(formData.value.school_id),
          role_id: toInt(formData.value.role_id),
          password: formData.value.password || null
        }
        break
      case 'teacher':
        endpoint = '/teachers'
        payload = {
          teacher_id: toInt(formData.value.teacher_id) || 0,
          name: formData.value.name,
          password: formData.value.password || null
        }
        break
      case 'course':
        endpoint = '/courses'
        payload = {
          course_id: formData.value.course_id,
          course_name: formData.value.course_name,
          teacher_id: formData.value.teacher_id,
          class_hours: formData.value.class_hours
        }
        break
      default:
        return
    }

    // Validation - check required fields per type
    if (props.type === 'leave' && !isEditMode) {
      if (!payload.student_id || !payload.leave_date || !payload.leave_hours || payload.leave_hours <= 0) {
        error.value = '请填写所有必填字段（学生ID、请假日期、请假课时，课时需大于0）'
        return
      }
    } else if (props.type === 'leave' && isEditMode) {
      if (!payload.leave_date || !payload.leave_hours || payload.leave_hours <= 0) {
        error.value = '请填写必填字段（请假日期、请假课时，课时需大于0）'
        return
      }
    } else if (Object.values(payload).some(value => value === '' || value === null)) {
      error.value = '请填写所有必填字段'
      return
    }

    // 编辑模式用PUT，创建模式用POST
    const result = isEditMode
      ? await http.put(endpoint, payload)
      : await http.post(endpoint, payload)

    // 如果是请假条创建，且有选中文件，则上传文件
    if (props.type === 'leave' && !isEditMode && proofFiles.value.length > 0) {
      // 尝试多种可能的ID字段名
      const leaveId = (result as any).leave_id || (result as any).id || (result as any)['leave_id']
      if (!leaveId) {
        error.value = '创建请假条成功，但无法获取请假ID'
        isSubmitting.value = false
        return
      }
      try {
        const uploadResult = await uploadLeaveFiles(leaveId, proofFiles.value) as any
        // 更新请假条的materials字段
        const filePaths = uploadResult.files.map((f: any) => f.file_path)
        await http.put(`/leaves/edit/${leaveId}`, {
          materials: filePaths.join(',')
        })
      } catch (uploadError: any) {
        console.error('文件上传失败:', uploadError)
        error.value = '请假条创建成功，但文件上传失败'
        setTimeout(() => {
          closeModal()
          props.onSuccess()
        }, 2000)
        return
      }
    }

    success.value = '创建成功'
    setTimeout(() => {
      closeModal()
      props.onSuccess()
    }, 1500)
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
    } else {
      error.value = detail || err.response?.data?.message || err.message || '创建失败，请稍后重试'
    }
  } finally {
    isSubmitting.value = false
  }
}

// Watch for modal open and type changes
watch(() => props.show, (newValue) => {
  if (newValue) {
    fetchOptions()
    // 编辑模式：使用editData填充表单
    if (props.editData) {
      formData.value = { ...getDefaultFormData(), ...props.editData }
    } else {
      formData.value = getDefaultFormData()
    }
  }
})

// 监听editData变化
watch(() => props.editData, (newData) => {
  if (newData && props.show) {
    formData.value = { ...getDefaultFormData(), ...newData }
  }
})

watch(() => props.type, () => {
  formData.value = getDefaultFormData()
  if (props.show) {
    fetchOptions()
  }
})

// When school changes for student form, refetch reviewers for that school
watch(() => formData.value.school_id, async (newSchoolId) => {
  if (props.type === 'student' && newSchoolId) {
    try {
      const res = await http.get('/reviewers', { params: { page_size: 100, school_id: newSchoolId } })
      reviewers.value = (res as any).items || []
    } catch (error) {
      console.error('获取辅导员列表失败:', error)
      reviewers.value = []
    }
  } else if (props.type === 'student' && !newSchoolId) {
    reviewers.value = []
  }
})

// Get current user ID for leave creation
const currentUserId = computed(() => {
  const id = localStorage.getItem('id')
  return id ? parseInt(id) : null
})

// Auto-fill student ID for leave creation if current user is a student
watch(() => props.type, (newType) => {
    if (newType === 'leave' && currentUserRole.value === 'student' && currentUserId.value) {
      formData.value.student_id = String(currentUserId.value)
    }
})

// Also auto-fill when modal opens
watch(() => props.show, (newValue) => {
  if (newValue && props.type === 'leave' && currentUserRole.value === 'student' && currentUserId.value) {
    formData.value.student_id = String(currentUserId.value)
  }
})
</script>

<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-content">
      <!-- <div class="modal-header">
        <h3>
          {{ type === 'leave' ? (editId ? '修改请假条' : '创建请假条') :
             type === 'student' ? '学生管理' :
             type === 'reviewer' ? '审核人管理' :
             type === 'teacher' ? '教师管理' : '课程管理' }}
        </h3>
      </div> -->

      <div class="modal-body">
        <!-- Import Section (only for non-leave types) -->

        <!-- Create Section -->
        <div class="create-section">
          <h4>{{ type === 'leave' ? '创建请假条' : '创建' + (type === 'student' ? '学生' : type === 'reviewer' ? '审核人' : type === 'teacher' ? '教师' : '课程') }}</h4>
          
          <!-- Leave Form -->
          <form v-if="type === 'leave'" @submit.prevent="handleCreate" class="create-form">
            <div class="form-row-two">
              <div class="form-group">
                <label for="student_id">
                  学生ID
                </label>
                <input type="number" id="student_id" v-model="formData.student_id"
                  :readonly="currentUserRole === 'student'" :disabled="currentUserRole === 'student'"
                  :class="{ 'readonly-input': currentUserRole === 'student' }" required
                  :placeholder="currentUserRole === 'student' ? `当前用户ID: ${currentUserId}` : '请输入学生ID'"
                  min="1" />
              </div>
              <div class="form-group">
                <label for="leave_date">请假日期 *</label>
                <input type="date" id="leave_date" v-model="formData.leave_date" required />
              </div>
            </div>

            <div class="form-group">
              <label for="guarantee_student_id">担保人学生ID（紧急请假可选）</label>
              <input type="number" id="guarantee_student_id" v-model="formData.guarantee_student_id"
                placeholder="填写担保人的学生ID，不填则走正常审批流程" min="1" />
            </div>
            
            <div class="form-group">
              <label for="course">课程</label>
              <select id="course" v-model="formData.course_id">
                <option value="0">请选择课程</option>
                <option v-if="loadingOptions" value="">加载中...</option>
                <option v-for="course in courses" :key="course.course_id" :value="course.course_id">
                  {{ course.course_name }} ({{ course.teacher_name }})
                </option>
              </select>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label for="leave_hours">请假课时 *</label>
                <input type="number" id="leave_hours" v-model="formData.leave_hours" required placeholder="数字" min="1" />
              </div>
              <div class="form-group">
                <label for="leave_type">请假类型</label>
                <select id="leave_type" v-model="formData.leave_type">
                  <option value="">请选择请假类型</option>
                  <option value="病假">病假</option>
                  <option value="事假">事假</option>
                  <option value="公假">公假</option>
                  <option value="其他">其他</option>
                </select>
              </div>
            </div>
            
            <div class="form-group">
              <label for="remarks">备注</label>
              <textarea id="remarks" v-model="formData.remarks" rows="3" placeholder="请输入请假事由等备注信息"
                maxlength="100"></textarea>
            </div>

            <div class="form-group">
              <label>上传证明材料（可多选）</label>
              <div class="proof-upload">
                <input type="file" multiple accept=".jpg,.jpeg,.png,.gif,.bmp,.pdf,.doc,.docx" @change="handleProofFileChange" />
                <button type="button" v-if="proofFiles.length > 0" @click="clearProofFiles" class="btn btn-secondary btn-sm">
                  清空已选文件
                </button>
              </div>
              <!-- Selected files list -->
              <div v-if="proofFiles.length > 0" class="selected-files">
                <div v-for="(file, index) in proofFiles" :key="index" class="file-item">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">({{ (file.size / 1024).toFixed(1) }}KB)</span>
                  <button type="button" @click="removeProofFile(index)" class="btn-remove">×</button>
                </div>
              </div>
              <div v-else class="uploaded-hint">未选择文件（提交请假条时可一并上传）</div>
            </div>

            <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? '创建中...' : '创建请假条' }}
            </button>
          </form>

          <!-- Student Form -->
          <form v-else-if="type === 'student'" @submit.prevent="handleCreate" class="create-form">
            <div class="form-row">
              <div class="form-group">
                <label>学号</label>
                <input type="text" v-model="formData.student_id" readonly class="readonly-input" />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.student_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系 *</label>
                <select v-model="formData.school_id" required>
                  <option value="">请选择院系</option>
                  <option v-if="loadingOptions" value="">加载中...</option>
                  <option v-for="school in schools" :key="school.school_id" :value="school.school_id">
                    {{ school.school_name }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>辅导员</label>
                <select v-model="formData.reviewer_id" :disabled="!formData.school_id">
                  <option value="">请先选择院系</option>
                  <option v-if="loadingOptions" value="">加载中...</option>
                  <option v-for="reviewer in reviewers" :key="reviewer.reviewer_id" :value="reviewer.reviewer_id">
                    {{ reviewer.reviewer_name }}
                  </option>
                </select>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>密码 *</label>
                <input type="password" v-model="formData.password" required />
              </div>
              <div class="form-group">
                <label>担保权限生效时间</label>
                <input type="date" v-model="formData.guarantee_permission" />
              </div>
            </div>
            
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? '创建中...' : '创建学生' }}
            </button>
          </form>

          <!-- Reviewer Form -->
          <form v-else-if="type === 'reviewer'" @submit.prevent="handleCreate" class="create-form">
            <div class="form-row">
              <div class="form-group">
                <label>审核人ID</label>
                <input type="text" v-model="formData.reviewer_id" readonly class="readonly-input" />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.reviewer_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系</label>
                <select v-model="formData.school_id">
                  <option value="">请选择院系</option>
                  <option v-if="loadingOptions" value="">加载中...</option>
                  <option v-for="school in schools" :key="school.school_id" :value="school.school_id">
                    {{ school.school_name }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>职务</label>
                <select v-model="formData.role_id">
                  <option value="">请选择职务</option>
                  <option v-if="loadingOptions" value="">加载中...</option>
                  <option v-for="role in roles" :key="role.role_id" :value="role.role_id">
                    {{ role.role_name }}
                  </option>
                </select>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>密码 *</label>
                <input type="password" v-model="formData.password" required />
              </div>
            </div>
            
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? '创建中...' : '创建审核人' }}
            </button>
          </form>

          <!-- Teacher Form -->
          <form v-else-if="type === 'teacher'" @submit.prevent="handleCreate" class="create-form">
            <div class="form-row">
              <div class="form-group">
                <label>教师ID</label>
                <input type="text" v-model="formData.teacher_id" readonly class="readonly-input" />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>密码 *</label>
                <input type="password" v-model="formData.password" required />
              </div>
            </div>
            
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? '创建中...' : '创建教师' }}
            </button>
          </form>

          <!-- Course Form -->
          <form v-else-if="type === 'course'" @submit.prevent="handleCreate" class="create-form">
            <div class="form-row">
              <div class="form-group">
                <label>课程ID</label>
                <input type="text" v-model="formData.course_id" readonly class="readonly-input" />
              </div>
              <div class="form-group">
                <label>课程名称 *</label>
                <input type="text" v-model="formData.course_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>教师 *</label>
                <select v-model="formData.teacher_id" required>
                  <option value="">请选择教师</option>
                  <option v-if="loadingOptions" value="">加载中...</option>
                  <option v-for="teacher in teachers" :key="teacher.teacher_id" :value="teacher.teacher_id">
                    {{ teacher.teacher_name }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>课时 *</label>
                <input type="number" v-model="formData.class_hours" required min="1" />
              </div>
            </div>
            
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? '创建中...' : '创建课程' }}
            </button>
          </form>
        </div>

        <!-- Error and Success Messages -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        <div v-if="success" class="success-message">
          {{ success }}
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" @click="closeModal" class="btn btn-secondary">
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: var(--spacing);
}

.modal-content {
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--text-xl);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
}

.import-section {
  margin-bottom: var(--spacing-lg);
}

.import-section h4,
.create-section h4 {
  margin: 0 0 var(--spacing) 0;
  font-size: var(--text-lg);
  color: var(--text-primary);
}

.file-upload {
  display: flex;
  gap: var(--spacing);
  align-items: center;
}

.file-upload input[type="file"] {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-sm);
}

.divider {
  border: 0;
  border-top: 1px solid var(--border-light);
  margin: var(--spacing-lg) 0;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
}

.form-row-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  transition: border-color var(--transition);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary-600);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.readonly-input {
  background-color: var(--gray-100);
  cursor: not-allowed;
  color: var(--text-secondary);
}

.proof-upload {
  display: flex;
  gap: var(--spacing);
  align-items: center;
}

.proof-upload input[type="file"] {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-sm);
}

.uploaded-hint {
  font-size: var(--text-xs);
  color: #059669;
  margin-top: 0.25rem;
}

.btn-import {
  background-color: #10b981;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-import:hover {
  background-color: #059669;
}

.btn-download-template {
  display: inline-block;
  background-color: var(--primary-50, #eff6ff);
  color: var(--primary-600, #2563eb);
  border: 1px solid var(--primary-200, #bfdbfe);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all var(--transition);
}

.btn-download-template:hover {
  background-color: var(--primary-100, #dbeafe);
  border-color: var(--primary-400, #60a5fa);
}

.btn-import:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  align-self: flex-start;
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-primary:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-secondary {
  background-color: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-weight: 500;
  transition: all var(--transition);
}

.btn-secondary:hover {
  background-color: var(--gray-200);
  color: var(--text-primary);
  border-color: var(--border-dark);
}

.error-message {
  padding: var(--spacing);
  background-color: var(--error-light);
  color: var(--error);
  border: 1px solid #fca5a5;
  border-radius: var(--radius);
  font-size: var(--text-sm);
  margin-top: var(--spacing);
}

.success-message {
  padding: var(--spacing);
  background-color: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
  border-radius: var(--radius);
  font-size: var(--text-sm);
  margin-top: var(--spacing);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-light);
}

@media (max-width: 768px) {
  .form-row,
  .form-row-two {
    grid-template-columns: 1fr;
  }
  
  .file-upload {
    flex-direction: column;
    align-items: stretch;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .modal-footer button {
    width: 100%;
  }
  
  .btn-primary {
    align-self: stretch;
  }
}
</style>