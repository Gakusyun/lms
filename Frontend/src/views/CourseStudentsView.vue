<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStatusBadgeClass } from '../utils/formatters'
import http from '../utils/http'
import { createStudentCourse } from '../api'

// 获取路由参数
const router = useRouter()
const courseId = parseInt(useRoute().params.id as string)

// 返回课程列表页面
const goBackToCourses = () => {
  router.push('/courses')
}

// 数据状态
const students = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const courseName = ref('')
const currentUserRole = ref(localStorage.getItem('role') || '')
const isAdmin = computed(() => currentUserRole.value === 'admin')

// 添加学生相关状态
const showAddModal = ref(false)
const newStudentId = ref('')
const isSubmitting = ref(false)
const addError = ref('')
const addSuccess = ref('')

// 获取课程学生名单
const fetchCourseStudents = async () => {
  try {
    loading.value = true
    error.value = ''

    const data = await http.get(`/student-courses/course/${courseId}`) as any[]
    students.value = data

    // 从第一个学生的记录中获取课程名称
    if (data.length > 0 && data[0]?.course_name) {
      courseName.value = data[0].course_name
    } else {
      courseName.value = `课程 ${courseId}`
    }

    console.log(`课程 ${courseId} 的学生名单:`, students.value)
  } catch (err: any) {
    console.error('获取课程学生名单失败:', err)
    error.value = '获取课程学生名单失败，请重试'
  } finally {
    loading.value = false
  }
}

// 打开添加学生弹窗
const openAddModal = () => {
  showAddModal.value = true
  newStudentId.value = ''
  addError.value = ''
  addSuccess.value = ''
}

// 关闭弹窗
const closeAddModal = () => {
  showAddModal.value = false
  newStudentId.value = ''
  addError.value = ''
  addSuccess.value = ''
}

// 添加学生到课程
const handleAddStudent = async () => {
  if (!newStudentId.value) {
    addError.value = '请输入学生ID'
    return
  }

  isSubmitting.value = true
  addError.value = ''
  addSuccess.value = ''

  try {
    await createStudentCourse({
      student_id: parseInt(newStudentId.value),
      course_id: courseId
    })
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

// 组件挂载时获取数据
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
    <div class="page-header">
      <div class="header-info">
        <h1 class="page-title">{{ courseName }} - 学生名单</h1>
      </div>
      <div class="header-buttons">
        <button v-if="isAdmin" @click="openAddModal" class="btn btn-primary">
          添加学生
        </button>
        <button @click="goBackToCourses" class="btn btn-secondary">
          返回课程列表
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
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
              <span :class="getStatusBadgeClass(item.status)" class="badge">
                {{ item.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
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
          <div v-if="addError" class="error-message">{{ addError }}</div>
          <div v-if="addSuccess" class="success-message">{{ addSuccess }}</div>
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
  padding: var(--spacing-xl);
}

.header-info {
  flex: 1;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: var(--text-xs);
  font-weight: 500;
  border-radius: var(--radius);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-primary);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-xl);
  box-shadow: var(--shadow-sm);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-buttons {
  display: flex;
  gap: var(--spacing);
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  border: none;
}

.btn-primary {
  background: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-700);
}

.btn-secondary {
  background: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
}

.btn-secondary:hover {
  background: var(--gray-200);
  color: var(--text-primary);
}

.loading, .empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--text-secondary);
}

.error {
  padding: var(--spacing);
  background: var(--error-light);
  color: var(--error);
  border-radius: var(--radius);
  margin-bottom: var(--spacing);
}

.table-container {
  overflow-x: auto;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th, .data-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-light);
}

.data-table th {
  background: var(--gray-50);
  font-weight: 600;
  font-size: var(--text-sm);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 400px;
  max-width: 90vw;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing);
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 { margin: 0; font-size: var(--text-lg); }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.modal-form { padding: var(--spacing); }
.form-group { margin-bottom: var(--spacing); }
.form-group label { display: block; margin-bottom: 0.25rem; font-size: var(--text-sm); font-weight: 500; }
.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  box-sizing: border-box;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing);
  padding: var(--spacing);
  border-top: 1px solid var(--border-light);
}

.error-message {
  padding: var(--spacing);
  background: var(--error-light);
  color: var(--error);
  border-radius: var(--radius);
  font-size: var(--text-sm);
}

.success-message {
  padding: var(--spacing);
  background: #dcfce7;
  color: #166534;
  border-radius: var(--radius);
  font-size: var(--text-sm);
}
</style>