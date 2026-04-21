<script setup lang="ts">
import { ref } from 'vue'
import GenericList from '../components/GenericList.vue'
import http from '../utils/http'

const showCreateModal = ref(false)
const newSchoolName = ref('')
const isCreating = ref(false)
const createError = ref('')
const createSuccess = ref('')

const openCreateModal = () => {
  showCreateModal.value = true
  newSchoolName.value = ''
  createError.value = ''
  createSuccess.value = ''
}

const closeCreateModal = () => {
  showCreateModal.value = false
  newSchoolName.value = ''
  createError.value = ''
  createSuccess.value = ''
}

const handleCreate = async () => {
  if (!newSchoolName.value.trim()) {
    createError.value = '请输入部门名称'
    return
  }
  isCreating.value = true
  createError.value = ''
  createSuccess.value = ''
  try {
    await http.post('/schools', { school_name: newSchoolName.value.trim() })
    createSuccess.value = '创建成功'
    setTimeout(() => {
      closeCreateModal()
      window.location.reload()
    }, 1500)
  } catch (e: any) {
    createError.value = e.response?.data?.detail || '创建失败'
  } finally {
    isCreating.value = false
  }
}

const handleDownloadTemplate = async () => {
  try {
    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.DEV
      ? 'http://localhost:8000/api/v1'
      : (import.meta.env.VITE_API_BASE_URL || 'https://lms.gxj62.cn/api/v1')

    const response = await fetch(`${baseURL}/schools/import/template`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error(`下载失败: ${response.status}`)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'school_import_template.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e: any) {
    alert('模板下载失败: ' + e.message)
  }
}

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return
  importFile(input.files[0])
  input.value = ''
}

const isImporting = ref(false)
const importError = ref('')
const importSuccess = ref('')

const importFile = async (file: File) => {
  isImporting.value = true
  importError.value = ''
  importSuccess.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const result = await http.post('/schools/import', formData) as any
    if (result.errors && result.errors.length > 0) {
      importError.value = `导入完成，成功 ${result.imported} 条，失败 ${result.errors.length} 条`
    } else {
      importSuccess.value = `成功导入 ${result.imported} 条部门`
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
      endpoint="/schools"
      title="部门列表"
      :columns="[
        { key: 'school_id', label: '部门ID' },
        { key: 'school_name', label: '部门名称' }
      ]"
      item-label="个部门"
      :show-actions="false"
      hide-export
    >
      <template #header-buttons>
        <button class="btn btn-outline" @click="handleDownloadTemplate">下载模板</button>
        <label class="btn btn-secondary import-label">
          {{ isImporting ? '导入中...' : '批量导入' }}
          <input type="file" accept=".xlsx,.xls,.csv" @change="handleFileChange" :disabled="isImporting" hidden />
        </label>
        <button class="btn btn-primary" @click="openCreateModal">创建部门</button>
      </template>
    </GenericList>

    <div v-if="importSuccess" class="alert alert-success">{{ importSuccess }}</div>
    <div v-if="importError" class="alert alert-danger">{{ importError }}</div>

    <!-- 创建部门弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>创建部门</h3>
          <button class="close-btn" @click="closeCreateModal">×</button>
        </div>
        <div class="modal-form">
          <div class="form-group">
            <label>部门名称</label>
            <input v-model="newSchoolName" type="text" placeholder="请输入部门名称" @keyup.enter="handleCreate" />
          </div>
          <div v-if="createError" class="error-message">{{ createError }}</div>
          <div v-if="createSuccess" class="success-message">{{ createSuccess }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeCreateModal">取消</button>
          <button class="btn btn-primary" @click="handleCreate" :disabled="isCreating">
            {{ isCreating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.alert {
  padding: var(--spacing);
  border-radius: var(--radius);
  margin-bottom: var(--spacing);
  font-size: var(--text-sm);
}
.alert-success { background: #dcfce7; color: #166534; }
.alert-danger { background: var(--error-light); color: var(--error); }

.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; justify-content: center;
  align-items: center; z-index: 1000;
}
.modal-content {
  background: var(--bg-primary); border-radius: var(--radius-lg);
  width: 400px; max-width: 90vw;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--spacing); border-bottom: 1px solid var(--border-light);
}
.modal-header h3 { margin: 0; font-size: var(--text-lg); }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.modal-form { padding: var(--spacing); }
.form-group { margin-bottom: var(--spacing); }
.form-group label { display: block; margin-bottom: 0.25rem; font-size: var(--text-sm); font-weight: 500; }
.form-group input {
  width: 100%; padding: 0.5rem; border: 1px solid var(--border-medium);
  border-radius: var(--radius); box-sizing: border-box;
}
.modal-footer {
  display: flex; justify-content: flex-end; gap: var(--spacing);
  padding: var(--spacing); border-top: 1px solid var(--border-light);
}
.error-message { padding: var(--spacing); background: var(--error-light); color: var(--error); border-radius: var(--radius); font-size: var(--text-sm); }
.success-message { padding: var(--spacing); background: #dcfce7; color: #166534; border-radius: var(--radius); font-size: var(--text-sm); }
</style>
