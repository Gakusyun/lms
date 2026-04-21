<script setup lang="ts">
import { ref, computed } from 'vue'
import GenericList from '../components/GenericList.vue'
import ChangePasswordModal from '../components/ChangePasswordModal.vue'
import http from '../utils/http'

// 当前用户角色
const currentUserRole = computed(() => localStorage.getItem('role'))

// 是否为管理员
const isAdmin = computed(() => currentUserRole.value === 'admin')

// 下载导入模板
const isDownloadingTemplate = ref(false)
const handleDownloadTemplate = async () => {
  try {
    isDownloadingTemplate.value = true
    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.DEV
      ? 'http://localhost:8000/api/v1'
      : (import.meta.env.VITE_API_BASE_URL || 'https://lms.gxj62.cn/api/v1')

    const response = await fetch(`${baseURL}/teachers/import/template`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error(`下载失败: ${response.status}`)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'teacher_import_template.xlsx')
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
    const result = await http.post('/teachers/import', formData) as any
    if (result.errors && result.errors.length > 0) {
      importError.value = `导入完成，成功 ${result.imported} 条，失败 ${result.errors.length} 条`
    } else {
      importSuccess.value = `成功导入 ${result.imported} 条教师`
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

// 修改密码模态框状态
const showPasswordModal = ref(false)
const selectedUser = ref<{ id: number; name: string } | null>(null)

// 打开修改密码模态框
const openChangePassword = (item: any) => {
  selectedUser.value = {
    id: item.teacher_id,
    name: item.teacher_name
  }
  showPasswordModal.value = true
}

// 关闭修改密码模态框
const closePasswordModal = () => {
  showPasswordModal.value = false
  selectedUser.value = null
}

// 修改密码成功回调
const onPasswordChanged = () => {
  // 可以显示成功消息或刷新列表
  console.log('密码修改成功')
}
</script>

<template>
  <div>
    <GenericList
      endpoint="/teachers"
      title="教师列表"
      :columns="[
        { key: 'teacher_id', label: '教师ID' },
        { key: 'teacher_name', label: '姓名' }
      ]"
      item-label="名教师"
      :show-actions="isAdmin"
      :show-create="isAdmin"
      create-type="teacher"
    >
      <template #header-buttons>
        <button class="btn btn-outline" @click="handleDownloadTemplate" :disabled="isDownloadingTemplate">
          {{ isDownloadingTemplate ? '下载中...' : '下载模板' }}
        </button>
        <label class="btn btn-secondary import-label">
          {{ isImporting ? '导入中...' : '批量导入' }}
          <input type="file" accept=".xlsx,.xls,.csv" @change="handleFileChange" :disabled="isImporting" hidden />
        </label>
      </template>
      <template #actions="{ item }">
        <button
          v-if="isAdmin"
          @click="openChangePassword(item)"
          class="btn btn-sm btn-outline"
          title="修改密码"
        >
          修改密码
        </button>
      </template>
    </GenericList>

    <!-- 修改密码模态框 -->
    <ChangePasswordModal
      :show="showPasswordModal"
      :user-id="selectedUser?.id"
      :user-name="selectedUser?.name"
      @close="closePasswordModal"
      @success="onPasswordChanged"
    />

    <div v-if="importSuccess" class="alert alert-success">{{ importSuccess }}</div>
    <div v-if="importError" class="alert alert-danger">{{ importError }}</div>
  </div>
</template>

<style scoped>
.btn-sm {
  padding: 0.25rem 0.5rem;
}
</style>