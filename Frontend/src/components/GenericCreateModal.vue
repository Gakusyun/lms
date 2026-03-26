<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import http from '../utils/http'

interface Props {
  show: boolean
  type: 'leave' | 'student' | 'reviewer' | 'teacher' | 'course'
  onClose: () => void
  onSuccess: () => void
  itemLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  itemLabel: ''
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

// Options for select fields
const reviewers = ref<any[]>([])
const teachers = ref<any[]>([])
const courses = ref<any[]>([])
const loadingOptions = ref(false)

// Get options data
const fetchOptions = async () => {
  loadingOptions.value = true
  try {
    if (props.type === 'student') {
      const response = await http.get('/reviewers')
      reviewers.value = response.data.items || []
    } else if (props.type === 'course') {
      const response = await http.get('/teachers')
      teachers.value = response.data.items || []
    } else if (props.type === 'leave') {
      const response = await http.get('/courses')
      courses.value = response.data.items || []
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
  
  // Reset form data
  formData.value = getDefaultFormData()
}

// Get default form data based on type
const getDefaultFormData = () => {
  switch (props.type) {
    case 'leave':
      return {
        student_id: null,
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
        school: '',
        reviewer_id: '',
        password: '',
        guarantee_permission: ''
      }
    case 'reviewer':
      return {
        reviewer_id: '',
        reviewer_name: '',
        school: '',
        password: ''
      }
    case 'teacher':
      return {
        teacher_id: '',
        teacher_name: '',
        school: '',
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
const formData = ref(getDefaultFormData())

// Handle file change
const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    file.value = target.files[0]
  }
}

// Handle import
const handleImport = async () => {
  if (!file.value) {
    error.value = '请选择要导入的文件'
    return
  }

  try {
    isUploading.value = true
    error.value = ''
    success.value = ''

    const formData = new FormData()
    formData.append('file', file.value)

    let endpoint = ''
    switch (props.type) {
      case 'student':
        endpoint = '/students/import'
        break
      case 'reviewer':
        endpoint = '/reviewers/import'
        break
      case 'teacher':
        endpoint = '/teachers/import'
        break
      case 'course':
        endpoint = '/courses/import'
        break
      default:
        return
    }

    await http.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    success.value = '导入成功'
    setTimeout(() => {
      closeModal()
      props.onSuccess()
    }, 1500)
  } catch (error: any) {
    console.error('导入失败:', error)
    error.value = error.response?.data?.message || error.message || '导入失败，请稍后重试'
  } finally {
    isUploading.value = false
  }
}

// Handle create
const handleCreate = async () => {
  try {
    isSubmitting.value = true
    error.value = ''
    success.value = ''

    let endpoint = ''
    let payload: any = {}

    switch (props.type) {
      case 'leave':
        endpoint = '/leaves'
        payload = {
          student_id: formData.value.student_id,
          course_id: formData.value.course_id === 0 ? null : formData.value.course_id,
          leave_date: formData.value.leave_date,
          leave_hours: formData.value.leave_hours,
          leave_type: formData.value.leave_type || null,
          remarks: formData.value.remarks || null
        }
        break
      case 'student':
        endpoint = '/students'
        payload = {
          student_id: formData.value.student_id,
          student_name: formData.value.student_name,
          school: formData.value.school,
          reviewer_id: formData.value.reviewer_id,
          password: formData.value.password,
          guarantee_permission: formData.value.guarantee_permission
        }
        break
      case 'reviewer':
        endpoint = '/reviewers'
        payload = {
          reviewer_id: formData.value.reviewer_id,
          reviewer_name: formData.value.reviewer_name,
          school: formData.value.school,
          password: formData.value.password
        }
        break
      case 'teacher':
        endpoint = '/teachers'
        payload = {
          teacher_id: formData.value.teacher_id,
          teacher_name: formData.value.teacher_name,
          school: formData.value.school,
          password: formData.value.password
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

    // Validation
    if (Object.values(payload).some(value => value === '' || value === null)) {
      error.value = '请填写所有必填字段'
      return
    }

    await http.post(endpoint, payload)

    success.value = '创建成功'
    setTimeout(() => {
      closeModal()
      props.onSuccess()
    }, 1500)
  } catch (error: any) {
    console.error('创建失败:', error)
    error.value = error.response?.data?.message || error.message || '创建失败，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}

// Watch for modal open and type changes
watch(() => props.show, (newValue) => {
  if (newValue) {
    fetchOptions()
    // Reset form when modal opens
    formData.value = getDefaultFormData()
  }
})

watch(() => props.type, () => {
  formData.value = getDefaultFormData()
  if (props.show) {
    fetchOptions()
  }
})

// Get current user ID for leave creation
const currentUserId = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    try {
      const user = JSON.parse(userInfo)
      return user.id
    } catch (e) {
      console.error('解析用户信息失败:', e)
    }
  }
  return null
})

// Auto-fill student ID for leave creation if current user is a student
watch(() => props.type, (newType) => {
  if (newType === 'leave' && currentUserRole.value === 'student' && currentUserId.value) {
    formData.value.student_id = currentUserId.value
  }
})
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>
          {{ type === 'leave' ? '创建请假条' : 
             type === 'student' ? '学生管理' : 
             type === 'reviewer' ? '审核人管理' : 
             type === 'teacher' ? '教师管理' : '课程管理' }}
        </h3>
      </div>

      <div class="modal-body">
        <!-- Import Section (only for non-leave types) -->
        <div v-if="type !== 'leave'" class="import-section">
          <h4>批量导入</h4>
          <div class="file-upload">
            <input type="file" accept=".xlsx,.xls,.csv" @change="handleFileChange" />
            <button @click="handleImport" class="btn btn-import" :disabled="isUploading">
              {{ isUploading ? '导入中...' : '导入Excel' }}
            </button>
          </div>
        </div>

        <hr v-if="type !== 'leave'" class="divider" />

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
                <input type="number" id="leave_hours" v-model="formData.leave_hours" required placeholder="数字" />
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
            
            <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? '创建中...' : '创建请假条' }}
            </button>
          </form>

          <!-- Student Form -->
          <form v-else-if="type === 'student'" @submit.prevent="handleCreate" class="create-form">
            <div class="form-row">
              <div class="form-group">
                <label>学号 *</label>
                <input type="text" v-model="formData.student_id" required />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.student_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系 *</label>
                <input type="text" v-model="formData.school" required />
              </div>
              <div class="form-group">
                <label>审核人 *</label>
                <select v-model="formData.reviewer_id" required>
                  <option value="">请选择审核人</option>
                  <option v-if="loadingOptions" value="">加载中...</option>
                  <option v-for="reviewer in reviewers" :key="reviewer.reviewer_id" :value="reviewer.reviewer_id">
                    {{ reviewer.reviewer_name }} ({{ reviewer.school }})
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
                <label>审核人ID *</label>
                <input type="text" v-model="formData.reviewer_id" required />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.reviewer_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系 *</label>
                <input type="text" v-model="formData.school" required />
              </div>
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
                <label>教师ID *</label>
                <input type="text" v-model="formData.teacher_id" required />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.teacher_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系 *</label>
                <input type="text" v-model="formData.school" required />
              </div>
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
                <label>课程ID *</label>
                <input type="text" v-model="formData.course_id" required />
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
                    {{ teacher.teacher_name }} ({{ teacher.school }})
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