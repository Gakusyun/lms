<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStatusBadgeClass } from '../utils/formatters'
import http from '../utils/http'
import { createStudentCourse } from '../api'

const router = useRouter()
const courseId = parseInt(useRoute().params.id as string)

const goBackToCourses = () => {
  router.push('/courses')
}

const students = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const courseName = ref('')
const currentUserRole = ref(localStorage.getItem('role') || '')
const isAdmin = computed(() => currentUserRole.value === 'admin')

const showAddModal = ref(false)
const newStudentId = ref('')
const isSubmitting = ref(false)
const addError = ref('')
const addSuccess = ref('')

const fetchCourseStudents = async () => {
  try {
    loading.value = true
    error.value = ''
    const data = await http.get(`/student-courses/course/${courseId}`) as any[]
    students.value = data
    if (data.length > 0 && data[0]?.course_name) {
      courseName.value = data[0].course_name
    } else {
      courseName.value = `课程 ${courseId}`
    }
  } catch (err: any) {
    error.value = '获取课程学生名单失败，请重试'
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  showAddModal.value = true
  newStudentId.value = ''
  addError.value = ''
  addSuccess.value = ''
}

const closeAddModal = () => {
  showAddModal.value = false
}

const handleAddStudent = async () => {
  if (!newStudentId.value) {
    addError.value = '请输入学生ID'
    return
  }
  isSubmitting.value = true
  addError.value = ''
  addSuccess.value = ''
  try {
    await createStudentCourse({ student_id: parseInt(newStudentId.value), course_id: courseId })
    addSuccess.value = '添加成功'
    setTimeout(() => {
      closeAddModal()
      fetchCourseStudents()
    }, 1500)
  } catch (e: any) {
    addError.value = e.response?.data?.detail || '添加失败'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  if (courseId) {
    fetchCourseStudents()
  } else {
    error.value = '无效的课程ID'
  }
})
</script>

<template>
  <div class="course-students-page">
    <div class="container">
      <div class="page-header">
        <div class="header-info">
          <h1 class="page-title">{{ courseName }} - 学生名单</h1>
        </div>
        <div class="header-buttons">
          <button v-if="isAdmin" @click="openAddModal" class="btn btn-primary">添加学生</button>
          <button @click="goBackToCourses" class="btn btn-secondary">返回课程列表</button>
        </div>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-else-if="students.length === 0" class="empty-state">
        <p>暂无学生选课此课程</p>
      </div>
      <div v-else class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>学生ID</th>
              <th>学生姓名</th>
              <th>课程名称</th>
              <th>教师姓名</th>
              <th>选课日期</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in students" :key="item.student_id">
              <td>{{ item.student_id }}</td>
              <td>{{ item.student_name || '未知' }}</td>
              <td>{{ item.course_name || courseName }}</td>
              <td>{{ item.teacher_name || '未知' }}</td>
              <td>{{ item.enrollment_date || '-' }}</td>
              <td>
                <span :class="getStatusBadgeClass(item.status)" class="badge">{{ item.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 添加学生弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加学生到课程</h3>
          <button class="close-btn" @click="closeAddModal">×</button>
        </div>
        <div class="modal-form">
          <div class="form-group">
            <label>学生ID</label>
            <input v-model="newStudentId" type="number" placeholder="输入学生ID" />
          </div>
          <div v-if="addError" class="alert alert-danger">{{ addError }}</div>
          <div v-if="addSuccess" class="alert alert-success">{{ addSuccess }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeAddModal">取消</button>
          <button class="btn btn-primary" @click="handleAddStudent" :disabled="isSubmitting">
            {{ isSubmitting ? '添加中...' : '确定' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.course-students-page {
  min-height: 100vh;
  background: var(--bg-secondary);
  padding: var(--spacing-xl) 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
}

.alert {
  padding: var(--spacing);
  border-radius: var(--radius);
  margin-bottom: var(--spacing);
  font-size: var(--text-sm);
}

.alert-danger {
  background: var(--error-light);
  color: var(--error);
  border: 1px solid #fca5a5;
}

.alert-success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #6ee7b7;
}
</style>
