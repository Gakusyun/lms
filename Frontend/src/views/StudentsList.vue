<script setup lang="ts">
import { ref, computed } from 'vue'
import GenericList from '../components/GenericList.vue'
import ChangePasswordModal from '../components/ChangePasswordModal.vue'
import { formatDate } from '../utils/formatters'
import { importStudents } from '../api'

// 当前用户角色
const currentUserRole = computed(() => localStorage.getItem('role'))

// 是否为管理员
const isAdmin = computed(() => currentUserRole.value === 'admin')
const isReviewer = computed(() => currentUserRole.value === 'reviewer')

// 修改密码模态框状态
const showPasswordModal = ref(false)
const selectedUser = ref<{ id: number; name: string } | null>(null)

// 打开修改密码模态框
const openChangePassword = (item: any) => {
  selectedUser.value = {
    id: item.student_id,
    name: item.student_name
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

// 下载导入模板
const isDownloadingTemplate = ref(false)
const handleDownloadTemplate = async () => {
  try {
    isDownloadingTemplate.value = true
    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.DEV
      ? 'http://localhost:8000/api/v1'
      : (import.meta.env.VITE_API_BASE_URL || 'https://lms.gxj62.cn/api/v1')

    const response = await fetch(`${baseURL}/students/import/template`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`)
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'student_import_template.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载模板失败:', error)
    alert('下载模板失败')
  } finally {
    isDownloadingTemplate.value = false
  }
}

// 导入学生相关
const isImporting = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    isImporting.value = true
    await importStudents(file)
    alert('导入成功')
    window.location.reload()
  } catch (error) {
    console.error('导入失败:', error)
    alert('导入失败')
  } finally {
    isImporting.value = false
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
}
</script>

<template>
  <div>
    <GenericList
      endpoint="/students"
      title="学生列表"
      :columns="[
        { key: 'student_id', label: '学号' },
        { key: 'student_name', label: '学生姓名' },
        { key: 'school_name', label: '院系' },
        { key: 'guarantee_permission', label: '担保权限生效时间', formatter: formatDate },
        { key: 'reviewer_id', label: '审核人ID' },
        { key: 'reviewer_name', label: '审核人姓名' }
      ]"
      item-label="名学生"
      :show-actions="isAdmin"
      :show-create="isAdmin || isReviewer"
      create-type="student"
    >
      <template #header-buttons>
        <button v-if="isAdmin" @click="handleDownloadTemplate" class="btn btn-outline" :disabled="isDownloadingTemplate">
          {{ isDownloadingTemplate ? '下载中...' : '下载模板' }}
        </button>
        <label v-if="isAdmin" class="btn btn-secondary import-label">
          {{ isImporting ? '导入中...' : '批量导入' }}
          <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" style="display: none" @change="handleFileChange" :disabled="isImporting" />
        </label>
          accept=".xlsx,.xls,.csv"
          style="display: none"
          @change="handleFileChange"
        />
      </template>
      <template #actions="{ item }">
        <button v-if="isAdmin" @click="openChangePassword(item)" class="btn btn-sm btn-outline" title="修改密码">
          修改密码
        </button>
      </template>
    </GenericList>

    <!-- 修改密码模态框 -->
    <ChangePasswordModal :show="showPasswordModal" :user-id="selectedUser?.id" :user-name="selectedUser?.name"
      @close="closePasswordModal" @success="onPasswordChanged" />
  </div>
</template>

<style scoped>
.btn {
  padding: 0.25rem 0.5rem;
  font-size: var(--text-xs);
  border-radius: var(--radius);
  border: 1px solid var(--border-medium);
  background-color: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.btn:hover {
  background-color: var(--gray-100);
  color: var(--text-primary);
  border-color: var(--border-dark);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
}

.btn-outline {
  border: 1px solid var(--border-medium);
}

</style>