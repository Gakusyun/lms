<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { formatDate } from '../utils/formatters'

interface AuditLog {
  log_id: number
  user_id: number
  user_role: string
  user_name?: string
  action: string
  target_type?: string
  target_id?: number
  detail?: string
  ip_address?: string
  timestamp: string
}

interface AuditAction {
  code: string
  name: string
}

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)
const totalItems = ref(0)
const totalPages = ref(0)
const logs = ref<AuditLog[]>([])
const loading = ref(false)

// 筛选状态
const filterForm = ref({
  user_role: '',
  action: '',
  start_date: '',
  end_date: '',
})

// 可选的操作类型
const actionTypes = ref<AuditAction[]>([])
const userRoles = ['admin', 'reviewer', 'teacher', 'student']

// 加载审计日志
const fetchAuditLogs = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    if (filterForm.value.user_role) params.user_role = filterForm.value.user_role
    if (filterForm.value.action) params.action = filterForm.value.action
    if (filterForm.value.start_date) params.start_date = filterForm.value.start_date
    if (filterForm.value.end_date) params.end_date = filterForm.value.end_date

    const response = await fetch(`/api/v1/audit-logs?${new URLSearchParams(params as any).toString()}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })

    if (response.ok) {
      const data = await response.json()
      logs.value = data.items || []
      totalItems.value = data.total || 0
      totalPages.value = data.total_pages || 0
    }
  } catch (error) {
    console.error('获取审计日志失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载操作类型
const fetchActionTypes = async () => {
  try {
    const response = await fetch('/api/v1/audit-logs/actions', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    if (response.ok) {
      const data = await response.json()
      actionTypes.value = data.actions || []
    }
  } catch (error) {
    console.error('获取操作类型失败:', error)
  }
}

// 搜索/筛选
const handleSearch = () => {
  currentPage.value = 1
  fetchAuditLogs()
}

// 重置筛选
const handleReset = () => {
  filterForm.value = {
    user_role: '',
    action: '',
    start_date: '',
    end_date: '',
  }
  handleSearch()
}

// 翻页
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchAuditLogs()
}

// 导出审计日志
const handleExport = async () => {
  try {
    const params: any = {}
    if (filterForm.value.user_role) params.user_role = filterForm.value.user_role
    if (filterForm.value.action) params.action = filterForm.value.action
    if (filterForm.value.start_date) params.start_date = filterForm.value.start_date
    if (filterForm.value.end_date) params.end_date = filterForm.value.end_date

    const query = new URLSearchParams(params as any).toString()
    const response = await fetch(`/api/v1/audit-logs?page=1&page_size=10000${query ? '&' + query : ''}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })

    if (response.ok) {
      const data = await response.json()
      const json = JSON.stringify(data.items, null, 2)
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (error) {
    console.error('导出失败:', error)
  }
}

// 格式化操作名称
const formatAction = (action: string): string => {
  const actionMap: Record<string, string> = {
    login: '登录',
    logout: '登出',
    password_change: '修改密码',
    leave_create: '创建请假',
    leave_edit: '编辑请假',
    leave_approve: '批准请假',
    leave_reject: '拒绝请假',
    leave_cancel: '撤销请假',
    leave_batch_approve: '批量批准请假',
    leave_batch_reject: '批量拒绝请假',
    user_create: '创建用户',
    user_update: '更新用户',
    user_delete: '删除用户',
    data_export: '数据导出',
    data_backup: '数据备份',
    data_restore: '数据恢复',
  }
  return actionMap[action] || action.replace(/_/g, ' ')
}

// 格式化角色名称
const formatRole = (role: string): string => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    reviewer: '审核员',
    teacher: '教师',
    student: '学生',
  }
  return roleMap[role] || role
}

onMounted(() => {
  fetchAuditLogs()
  fetchActionTypes()
})
</script>

<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h1>审计日志</h1>
      <button class="btn btn-primary" @click="handleExport">导出 JSON</button>
    </div>

    <!-- 筛选表单 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-group">
          <label>用户角色</label>
          <select v-model="filterForm.user_role">
            <option value="">全部</option>
            <option v-for="role in userRoles" :key="role" :value="role">
              {{ formatRole(role) }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>操作类型</label>
          <select v-model="filterForm.action">
            <option value="">全部</option>
            <option v-for="act in actionTypes" :key="act.code" :value="act.code">
              {{ act.name }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>开始时间</label>
          <input type="datetime-local" v-model="filterForm.start_date" />
        </div>

        <div class="filter-group">
          <label>结束时间</label>
          <input type="datetime-local" v-model="filterForm.end_date" />
        </div>

        <div class="filter-actions">
          <button class="btn btn-primary" @click="handleSearch">搜索</button>
          <button class="btn btn-secondary" @click="handleReset">重置</button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 数据表格 -->
    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>日志ID</th>
            <th>时间</th>
            <th>用户</th>
            <th>角色</th>
            <th>操作</th>
            <th>目标类型</th>
            <th>目标ID</th>
            <th>详情</th>
            <th>IP地址</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.log_id">
            <td>{{ log.log_id }}</td>
            <td>{{ formatDate(log.timestamp) }}</td>
            <td>{{ log.user_name || `ID:${log.user_id}` }}</td>
            <td><span class="role-badge" :class="log.user_role">{{ formatRole(log.user_role) }}</span></td>
            <td><span class="action-badge">{{ formatAction(log.action) }}</span></td>
            <td>{{ log.target_type || '-' }}</td>
            <td>{{ log.target_id || '-' }}</td>
            <td class="detail-cell">{{ log.detail || '-' }}</td>
            <td>{{ log.ip_address || '-' }}</td>
          </tr>
          <tr v-if="logs.length === 0">
            <td colspan="9" class="empty-row">暂无数据</td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          class="btn btn-sm"
          :disabled="currentPage === 1"
          @click="handlePageChange(currentPage - 1)"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ currentPage }} / {{ totalPages }} 页，共 {{ totalItems }} 条
        </span>
        <button
          class="btn btn-sm"
          :disabled="currentPage === totalPages"
          @click="handlePageChange(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audit-logs-page {
  padding: var(--spacing);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.filter-section {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.filter-row {
  display: flex;
  gap: var(--spacing);
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 160px;
}

.filter-group label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
}

.filter-group select,
.filter-group input {
  padding: 0.5rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.filter-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-end;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}

.table-container {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border-light);
  font-size: var(--text-sm);
}

.data-table th {
  background: var(--gray-50);
  font-weight: 600;
  color: var(--text-primary);
}

.data-table tbody tr:hover {
  background: var(--gray-50);
}

.empty-row {
  text-align: center;
  color: var(--text-secondary);
  padding: 2rem !important;
}

.detail-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-badge,
.action-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius);
  font-size: var(--text-xs);
  font-weight: 500;
}

.role-badge.admin { background: #fef3c7; color: #92400e; }
.role-badge.reviewer { background: #dbeafe; color: #1e40af; }
.role-badge.teacher { background: #d1fae5; color: #065f46; }
.role-badge.student { background: #ede9fe; color: #5b21b6; }

.action-badge {
  background: var(--gray-100);
  color: var(--text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-light);
}

.page-info {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
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
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: var(--text-sm);
}
</style>
