<script setup lang="ts">
import { ref, computed } from 'vue'
import { getCourseStudents, getStudentCourses, createStudentCourse, deleteStudentCourse } from '../api'
import http from '../utils/http'

const currentUserRole = computed(() => localStorage.getItem('role'))
const isAdmin = computed(() => currentUserRole.value === 'admin')

// 搜索/筛选
const searchStudentId = ref('')
const searchCourseId = ref('')
const filterMode = ref<'course' | 'student'>('course')

// 列表数据
const courseStudents = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')

// 课程和学生选项（用于新建关联）
const courses = ref<any[]>([])
const students = ref<any[]>([])
const showAddModal = ref(false)
const newStudentId = ref('')
const newCourseId = ref('')
const isSubmitting = ref(false)

// 加载课程列表
const loadCourses = async () => {
  try {
    const res: any = await http.get('/courses', { params: { page_size: 100 } })
    courses.value = res.items || []
  } catch (e) {
    console.error('加载课程失败', e)
  }
}

// 加载学生列表
const loadStudents = async () => {
  try {
    const res: any = await http.get('/students', { params: { page_size: 100 } })
    students.value = res.items || []
  } catch (e) {
    console.error('加载学生失败', e)
  }
}

// 加载选课数据
const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    if (filterMode.value === 'course' && searchCourseId.value) {
      const res: any = await getCourseStudents(parseInt(searchCourseId.value))
      courseStudents.value = res || []
    } else if (filterMode.value === 'student' && searchStudentId.value) {
      const res: any = await getStudentCourses(parseInt(searchStudentId.value))
      courseStudents.value = res || []
    } else {
      courseStudents.value = []
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

// 按课程ID筛选
const filterByCourse = () => {
  filterMode.value = 'course'
  searchStudentId.value = ''
  loadData()
}

// 按学生ID筛选
const filterByStudent = () => {
  filterMode.value = 'student'
  searchCourseId.value = ''
  loadData()
}

// 打开添加弹窗
const openAddModal = async () => {
  showAddModal.value = true
  newStudentId.value = ''
  newCourseId.value = ''
  await loadCourses()
  await loadStudents()
}

// 关闭弹窗
const closeAddModal = () => {
  showAddModal.value = false
}

// 添加选课记录
const handleAdd = async () => {
  if (!newStudentId.value || !newCourseId.value) {
    error.value = '请填写学生ID和课程ID'
    return
  }
  isSubmitting.value = true
  error.value = ''
  success.value = ''
  try {
    await createStudentCourse({
      student_id: parseInt(newStudentId.value),
      course_id: parseInt(newCourseId.value)
    })
    success.value = '添加成功'
    setTimeout(() => {
      closeAddModal()
      loadData()
    }, 1500)
  } catch (e: any) {
    error.value = e.response?.data?.detail || '添加失败'
  } finally {
    isSubmitting.value = false
  }
}

// 删除选课记录
const handleDelete = async (studentId: number, courseId: number) => {
  if (!confirm(`确认删除学生 ${studentId} 的课程 ${courseId} 选课记录？`)) return
  try {
    await deleteStudentCourse(studentId, courseId)
    success.value = '删除成功'
    loadData()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '删除失败'
  }
}
</script>

<template>
  <div class="list-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">学生选课管理</h1>
        <div class="header-buttons">
          <button v-if="isAdmin" @click="openAddModal" class="btn btn-primary">
            添加选课
          </button>
        </div>
      </div>

      <!-- 筛选区 -->
      <div class="filter-section">
        <div class="filter-tabs">
          <button :class="{ active: filterMode === 'course' }" @click="filterByCourse">按课程查看</button>
          <button :class="{ active: filterMode === 'student' }" @click="filterByStudent">按学生查看</button>
        </div>

        <div class="filter-inputs">
          <template v-if="filterMode === 'course'">
            <input v-model="searchCourseId" type="number" placeholder="输入课程ID" class="filter-input" />
            <button @click="loadData" class="btn btn-primary btn-sm">查询</button>
          </template>
          <template v-else>
            <input v-model="searchStudentId" type="number" placeholder="输入学生ID" class="filter-input" />
            <button @click="loadData" class="btn btn-primary btn-sm">查询</button>
          </template>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="success" class="success">{{ success }}</div>

      <div v-if="loading" class="loading">加载中...</div>

      <div v-else-if="courseStudents.length === 0" class="empty-state">
        <p>暂无选课数据，请通过筛选条件查询</p>
      </div>

      <div v-else class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>学生ID</th>
              <th>学生姓名</th>
              <th>课程ID</th>
              <th>课程名称</th>
              <th>教师姓名</th>
              <th>选课日期</th>
              <th>状态</th>
              <th v-if="isAdmin">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in courseStudents" :key="`${item.student_id}-${item.course_id}`">
              <td>{{ item.student_id }}</td>
              <td>{{ item.student_name || '-' }}</td>
              <td>{{ item.course_id }}</td>
              <td>{{ item.course_name || '-' }}</td>
              <td>{{ item.teacher_name || '-' }}</td>
              <td>{{ item.enrollment_date || '-' }}</td>
              <td>{{ item.status }}</td>
              <td v-if="isAdmin">
                <button class="btn btn-danger btn-sm" @click="handleDelete(item.student_id, item.course_id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 添加选课弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加选课</h3>
          <button class="close-btn" @click="closeAddModal">×</button>
        </div>
        <div class="modal-form">
          <div class="form-group">
            <label>学生ID</label>
            <input v-model="newStudentId" type="number" placeholder="输入学生ID" />
          </div>
          <div class="form-group">
            <label>课程ID</label>
            <input v-model="newCourseId" type="number" placeholder="输入课程ID" />
          </div>
          <div v-if="error" class="error-message">{{ error }}</div>
          <div v-if="success" class="success-message">{{ success }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeAddModal">取消</button>
          <button class="btn btn-primary" @click="handleAdd" :disabled="isSubmitting">
            {{ isSubmitting ? '提交中...' : '确定' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-page {
  min-height: 100vh;
  background-color: var(--bg-secondary);
  padding: var(--spacing-lg) 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}
.page-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.header-buttons {
  display: flex;
  gap: var(--spacing);
}
.filter-section {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing);
  margin-bottom: var(--spacing-lg);
}
.filter-tabs {
  display: flex;
  gap: var(--spacing);
  margin-bottom: var(--spacing);
}
.filter-tabs button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-medium);
  background: var(--gray-50);
  border-radius: var(--radius);
  cursor: pointer;
}
.filter-tabs button.active {
  background: var(--primary-600);
  color: white;
  border-color: var(--primary-600);
}
.filter-inputs {
  display: flex;
  gap: var(--spacing);
  align-items: center;
}
.filter-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-sm);
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
.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: var(--text-sm);
}
.btn-danger {
  background: #ef4444;
  color: white;
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
.success {
  padding: var(--spacing);
  background: #dcfce7;
  color: #166534;
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
