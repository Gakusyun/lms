<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getData } from '../api'
import { formatDateTime } from '../utils/formatters'
import { exportToExcel } from '../utils/excelExporter'
import http from '../utils/http'
import PaginationControls from '../components/PaginationControls.vue'

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

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)
const logs = ref<AuditLog[]>([])
const loading = ref(false)
const error = ref('')
const isExporting = ref(false)

// 筛选状态
const filterForm = ref({
  user_role: '',
  action: '',
  start_date: '',
  end_date: '',
})

const userRoles = ['admin', 'reviewer', 'teacher', 'student']

const router = useRouter()

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

// 加载审计日志
const fetchAuditLogs = async () => {
  loading.value = true
  error.value = ''
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    if (filterForm.value.user_role) params.user_role = filterForm.value.user_role
    if (filterForm.value.action) params.action = filterForm.value.action
    if (filterForm.value.start_date) params.start_date = filterForm.value.start_date
    if (filterForm.value.end_date) params.end_date = filterForm.value.end_date

    const response = await getData('/audit-logs', params) as any
    logs.value = response.items || []
    total.value = response.total || 0
    totalPages.value = response.total_pages || 0
  } catch (err: any) {
    error.value = err.message || '获取审计日志失败'
    console.error('获取审计日志失败:', err)
  } finally {
    loading.value = false
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

// 导出Excel
const handleExport = async () => {
  try {
    isExporting.value = true

    let allData: any[] = []
    let exportPage = 1
    let hasMore = true

    while (hasMore) {
      const params: any = { page: exportPage, page_size: 100 }
      if (filterForm.value.user_role) params.user_role = filterForm.value.user_role
      if (filterForm.value.action) params.action = filterForm.value.action
      if (filterForm.value.start_date) params.start_date = filterForm.value.start_date
      if (filterForm.value.end_date) params.end_date = filterForm.value.end_date

      const result: any = await http.get('/audit-logs', { params })
      const pageData = result.items || []
      allData = allData.concat(pageData)

      if (pageData.length < 100) {
        hasMore = false
      } else {
        exportPage++
      }
    }

    if (allData.length === 0) {
      alert('没有数据可以导出')
      return
    }

    const headers = ['日志ID', '时间', '用户', '角色', '操作', '目标类型', '目标ID', '详情', 'IP地址']
    const csvData = allData.map((item: any) => ({
      '日志ID': item.log_id,
      '时间': item.timestamp ? new Date(item.timestamp).toLocaleString('zh-CN') : '',
      '用户': item.user_name || `ID:${item.user_id}`,
      '角色': formatRole(item.user_role),
      '操作': formatAction(item.action),
      '目标类型': item.target_type || '',
      '目标ID': item.target_id || '',
      '详情': item.detail || '',
      'IP地址': item.ip_address || '',
    }))

    exportToExcel(csvData, '审计日志', headers)
  } catch (err: any) {
    console.error('导出失败:', err)
    alert(`导出失败: ${err.message || '未知错误'}`)
  } finally {
    isExporting.value = false
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  fetchAuditLogs()
})
</script>

<template>
  <div class="list-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">审计日志</h1>
        <div class="header-buttons">
          <button @click="handleExport" class="btn btn-export" :disabled="isExporting">
            {{ isExporting ? '导出中...' : '导出Excel' }}
          </button>
          <button @click="goBack" class="btn btn-back">返回首页</button>
        </div>
      </div>

      <!-- 筛选表单 -->
      <div class="stats-card">
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
              <option value="login">登录</option>
              <option value="logout">登出</option>
              <option value="password_change">修改密码</option>
              <option value="leave_create">创建请假</option>
              <option value="leave_edit">编辑请假</option>
              <option value="leave_approve">批准请假</option>
              <option value="leave_reject">拒绝请假</option>
              <option value="leave_cancel">撤销请假</option>
              <option value="user_create">创建用户</option>
              <option value="data_export">数据导出</option>
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
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <span>正在加载数据...</span>
      </div>

      <div v-else-if="error" class="error">
        <span>{{ error }}</span>
      </div>

      <div v-else class="page-content">
        <div class="stats-card">
          <p class="stats-text">共 {{ total }} 条日志 (第 {{ currentPage }} / {{ totalPages }} 页)</p>
        </div>

        <div v-if="logs.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>暂无审计日志数据</h3>
          <p>操作记录将在这里显示</p>
        </div>

        <div v-else class="data-section">
          <div class="table-container">
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
                <tr v-for="log in logs" :key="log.log_id" class="table-row">
                  <td class="table-cell">{{ log.log_id }}</td>
                  <td class="table-cell">{{ formatDateTime(log.timestamp) }}</td>
                  <td class="table-cell">{{ log.user_name || `ID:${log.user_id}` }}</td>
                  <td class="table-cell">
                    <span class="role-badge" :class="log.user_role">{{ formatRole(log.user_role) }}</span>
                  </td>
                  <td class="table-cell">{{ formatAction(log.action) }}</td>
                  <td class="table-cell">{{ log.target_type || '-' }}</td>
                  <td class="table-cell">{{ log.target_id || '-' }}</td>
                  <td class="table-cell detail-cell">{{ log.detail || '-' }}</td>
                  <td class="table-cell">{{ log.ip_address || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <PaginationControls
            :current-page="currentPage"
            :total-pages="totalPages"
            :total="total"
            :page-size="pageSize"
            :loading="loading"
            @page-change="handlePageChange"
          />
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
  padding-bottom: var(--spacing);
  border-bottom: 1px solid var(--border-light);
}

.header-buttons {
  display: flex;
  gap: var(--spacing);
}

.page-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.stats-card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing);
  box-shadow: var(--shadow);
}

.stats-text {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
  font-weight: 500;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--text-secondary);
  gap: var(--spacing);
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--border-light);
  border-top: 2px solid var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--error);
  background-color: var(--error-light);
  border: 1px solid #fca5a5;
  border-radius: var(--radius-lg);
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing);
  opacity: 0.5;
}

.empty-state h3 {
  font-size: var(--text-xl);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.empty-state p {
  color: var(--text-secondary);
  margin: 0;
}

.data-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.table-container {
  overflow-x: auto;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-light);
}

.data-table th {
  background-color: var(--gray-50);
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-medium);
  font-size: var(--text-sm);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table td {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.table-row {
  transition: background-color var(--transition-fast);
}

.table-row:hover {
  background-color: var(--gray-50);
}

.table-row:last-child .table-cell {
  border-bottom: none;
}

.table-cell {
  position: relative;
  vertical-align: middle;
}

.detail-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Filter row */
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
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.filter-group select:focus,
.filter-group input:focus {
  outline: none;
  border-color: var(--primary-600);
}

.filter-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-end;
}

/* Role badges */
.role-badge {
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

/* Buttons */
.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  font-size: var(--text-sm);
  border: none;
}

.btn-back {
  background-color: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
}

.btn-back:hover {
  background-color: var(--gray-200);
  color: var(--text-primary);
  border-color: var(--border-dark);
}

.btn-export {
  background-color: #10b981;
  color: white;
}

.btn-export:hover {
  background-color: #059669;
}

.btn-export:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
}

.btn-secondary:hover {
  background-color: var(--gray-200);
  color: var(--text-primary);
  border-color: var(--border-dark);
}

/* Responsive */
@media (max-width: 768px) {
  .list-page {
    padding: var(--spacing) 0;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing);
  }

  .page-title {
    font-size: var(--text-2xl);
    text-align: center;
  }

  .data-table th,
  .data-table td {
    padding: 0.75rem 0.5rem;
    font-size: var(--text-xs);
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-group {
    min-width: 100%;
  }
}
</style>
