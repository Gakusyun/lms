<script setup lang="ts">
import { ref, computed } from 'vue'
import http from '../utils/http'

interface Props {
  show: boolean
  type: 'student' | 'reviewer' | 'teacher' | 'course'
  onClose: () => void
  onSuccess: () => void
}

const props = defineProps<Props>()




// Modal state
const isSubmitting = ref(false)
const error = ref('')
const success = ref('')

// Form data
const formData = ref({
  // Student form
  student: {
    student_id: '',
    student_name: '',
    school: '',
    reviewer_id: '',
    password: '',
    guarantee_permission: ''
  },
  // Reviewer form
  reviewer: {
    reviewer_id: '',
    reviewer_name: '',
    school: '',
    password: ''
  },
  // Teacher form
  teacher: {
    teacher_id: '',
    teacher_name: '',
    school: '',
    password: ''
  },
  // Course form
  course: {
    course_id: '',
    course_name: '',
    teacher_id: '',
    class_hours: ''
  }
})

// File upload state
const file = ref<File | null>(null)
const isUploading = ref(false)

// Options for select fields
const reviewers = ref<any[]>([])
const teachers = ref<any[]>([])
const loadingOptions = ref(false)

// Get options data
const fetchOptions = async () => {
  if (props.type === 'student') {
    try {
      loadingOptions.value = true
      const response = await http.get('/reviewers')
      reviewers.value = response.data.items || []
    } catch (error) {
      console.error('获取审核人列表失败:', error)
    } finally {
      loadingOptions.value = false
    }
  } else if (props.type === 'course') {
    try {
      loadingOptions.value = true
      const response = await http.get('/teachers')
      teachers.value = response.data.items || []
    } catch (error) {
      console.error('获取教师列表失败:', error)
    } finally {
      loadingOptions.value = false
    }
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
  formData.value = {
    student: {
      student_id: '',
      student_name: '',
      school: '',
      reviewer_id: '',
      password: '',
      guarantee_permission: ''
    },
    reviewer: {
      reviewer_id: '',
      reviewer_name: '',
      school: '',
      password: ''
    },
    teacher: {
      teacher_id: '',
      teacher_name: '',
      school: '',
      password: ''
    },
    course: {
      course_id: '',
      course_name: '',
      teacher_id: '',
      class_hours: ''
    }
  }
}

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
      case 'student':
        endpoint = '/students'
        payload = {
          student_id: formData.value.student.student_id,
          student_name: formData.value.student.student_name,
          school: formData.value.student.school,
          reviewer_id: formData.value.student.reviewer_id,
          password: formData.value.student.password,
          guarantee_permission: formData.value.student.guarantee_permission
        }
        break
      case 'reviewer':
        endpoint = '/reviewers'
        payload = {
          reviewer_id: formData.value.reviewer.reviewer_id,
          reviewer_name: formData.value.reviewer.reviewer_name,
          school: formData.value.reviewer.school,
          password: formData.value.reviewer.password
        }
        break
      case 'teacher':
        endpoint = '/teachers'
        payload = {
          teacher_id: formData.value.teacher.teacher_id,
          teacher_name: formData.value.teacher.teacher_name,
          school: formData.value.teacher.school,
          password: formData.value.teacher.password
        }
        break
      case 'course':
        endpoint = '/courses'
        payload = {
          course_id: formData.value.course.course_id,
          course_name: formData.value.course.course_name,
          teacher_id: formData.value.course.teacher_id,
          class_hours: formData.value.course.class_hours
        }
        break
    }

    // Validation
    if (Object.values(payload).some(value => value === '')) {
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

// Watch for modal open
const isModalOpen = computed(() => props.show)
if (isModalOpen.value) {
  fetchOptions()
}
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>
          {{ type === 'student' ? '学生管理' : 
             type === 'reviewer' ? '审核人管理' : 
             type === 'teacher' ? '教师管理' : '课程管理' }}
        </h3>
      </div>

      <div class="modal-body">
        <!-- Import Section -->
        <div class="import-section">
          <h4>批量导入</h4>
          <div class="file-upload">
            <input type="file" accept=".xlsx,.xls,.csv" @change="handleFileChange" />
            <button @click="handleImport" class="btn btn-import" :disabled="isUploading">
              {{ isUploading ? '导入中...' : '导入Excel' }}
            </button>
          </div>
        </div>

        <hr class="divider" />

        <!-- Create Section -->
        <div class="create-section">
          <h4>创建{{ type === 'student' ? '学生' : type === 'reviewer' ? '审核人' : type === 'teacher' ? '教师' : '课程' }}</h4>
          
          <!-- Student Form -->
          <form v-if="type === 'student'" @submit.prevent="handleCreate" class="create-form">
            <div class="form-row">
              <div class="form-group">
                <label>学号 *</label>
                <input type="text" v-model="formData.student.student_id" required />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.student.student_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系 *</label>
                <input type="text" v-model="formData.student.school" required />
              </div>
              <div class="form-group">
                <label>审核人 *</label>
                <select v-model="formData.student.reviewer_id" required>
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
                <input type="password" v-model="formData.student.password" required />
              </div>
              <div class="form-group">
                <label>担保权限到期时间</label>
                <input type="date" v-model="formData.student.guarantee_permission" />
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
                <input type="text" v-model="formData.reviewer.reviewer_id" required />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.reviewer.reviewer_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系 *</label>
                <input type="text" v-model="formData.reviewer.school" required />
              </div>
              <div class="form-group">
                <label>密码 *</label>
                <input type="password" v-model="formData.reviewer.password" required />
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
                <input type="text" v-model="formData.teacher.teacher_id" required />
              </div>
              <div class="form-group">
                <label>姓名 *</label>
                <input type="text" v-model="formData.teacher.teacher_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>院系 *</label>
                <input type="text" v-model="formData.teacher.school" required />
              </div>
              <div class="form-group">
                <label>密码 *</label>
                <input type="password" v-model="formData.teacher.password" required />
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
                <input type="text" v-model="formData.course.course_id" required />
              </div>
              <div class="form-group">
                <label>课程名称 *</label>
                <input type="text" v-model="formData.course.course_name" required />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>教师 *</label>
                <select v-model="formData.course.teacher_id" required>
                  <option value="">请选择教师</option>
                  <option v-if="loadingOptions" value="">加载中...</option>
                  <option v-for="teacher in teachers" :key="teacher.teacher_id" :value="teacher.teacher_id">
                    {{ teacher.teacher_name }} ({{ teacher.school }})
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>课时 *</label>
                <input type="number" v-model="formData.course.class_hours" required min="1" />
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
.form-group select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  transition: border-color var(--transition);
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-600);
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
  font-weight: 500;
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
  .form-row {
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