<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import GenericList from '../components/GenericList.vue'
import http from '../utils/http'

const router = useRouter()

// 获取当前用户角色
const currentUserRole = computed(() => localStorage.getItem('role') || '')
const isAdmin = computed(() => currentUserRole.value === 'admin')

// 跳转到课程学生名单页面
const goToCourseStudents = (courseId: number) => {
  router.push(`/courses/${courseId}/students`)
}

// 下载导入模板
const isDownloadingTemplate = ref(false)
const handleDownloadTemplate = async () => {
  try {
    isDownloadingTemplate.value = true
    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.DEV
      ? 'http://localhost:8000/api/v1'
      : (import.meta.env.VITE_API_BASE_URL || 'https://lms.gxj62.cn/api/v1')

    const response = await fetch(`${baseURL}/courses/import/template`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error(`下载失败: ${response.status}`)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'course_import_template.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e: any) {
    alert('模板下载失败: ' + e.message)
  } finally {
    isDownloadingTemplate.value = false
  }
}

// 批量导入
const isImporting = ref(false)
const importError = ref('')
const importSuccess = ref('')

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return
  importFile(input.files[0])
  input.value = ''
}

const importFile = async (file: File) => {
  isImporting.value = true
  importError.value = ''
  importSuccess.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const result = await http.post('/courses/import', formData) as any
    if (result.errors && result.errors.length > 0) {
      importError.value = `导入完成，成功 ${result.imported} 条，失败 ${result.errors.length} 条`
    } else {
      importSuccess.value = `成功导入 ${result.imported} 条课程`
    }
    setTimeout(() => {
      if (!importError.value) window.location.reload()
    }, 2000)
  } catch (e: any) {
    importError.value = e.response?.data?.detail || '导入失败'
  } finally {
    isImporting.value = false
  }
}
</script>

<template>
  <div>
    <GenericList
      endpoint="/courses"
      title="课程列表"
      :show-actions="currentUserRole !== 'student'"
      :columns="[
        { key: 'course_id', label: '课程ID' },
        { key: 'course_name', label: '课程名称' },
        { key: 'class_hours', label: '课时' },
        { key: 'teacher_name', label: '教师姓名' },
        {
          key: 'enrollment_count',
          label: '选课人数',
          formatter: (value: any) => `${value || 0} 人`
        }
      ]"
      item-label="门课程"
      :show-create="isAdmin"
      create-type="course"
    >
      <template #header-buttons>
        <button v-if="isAdmin" class="btn btn-outline" @click="handleDownloadTemplate" :disabled="isDownloadingTemplate">
          {{ isDownloadingTemplate ? '下载中...' : '下载模板' }}
        </button>
        <label v-if="isAdmin" class="btn btn-secondary import-label">
          {{ isImporting ? '导入中...' : '批量导入' }}
          <input type="file" accept=".xlsx,.xls,.csv" @change="handleFileChange" :disabled="isImporting" hidden />
        </label>
      </template>
      <template #actions="{ item }">
        <button @click="goToCourseStudents(item.course_id)" class="btn btn-primary btn-sm">
          查看学生名单
        </button>
      </template>
    </GenericList>

    <div v-if="importSuccess" class="alert alert-success">{{ importSuccess }}</div>
    <div v-if="importError" class="alert alert-danger">{{ importError }}</div>
  </div>
</template>

