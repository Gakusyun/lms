<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../api'
import http from '../utils/http'

const router = useRouter()

interface NotificationItem {
  notification_id: number
  user_id: number
  title: string
  content: string
  is_read: boolean
  created_at: string
}

const notifications = ref<NotificationItem[]>([])
const loading = ref(true)
const error = ref('')
const currentPage = ref(1)
const totalPages = ref(0)
const total = ref(0)
const filter = ref<'all' | 'unread' | 'read'>('all')

const fetchNotifications = async () => {
  try {
    loading.value = true
    error.value = ''
    const params: any = { page: currentPage.value, page_size: 20 }
    if (filter.value === 'unread') params.is_read = false
    else if (filter.value === 'read') params.is_read = true

    const response = await getNotifications(params)
    notifications.value = response?.items || []
    total.value = response?.total || 0
    totalPages.value = response?.total_pages || 0
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取通知失败'
  } finally {
    loading.value = false
  }
}

const handleMarkRead = async (id: number) => {
  try {
    await markNotificationRead(id)
    const item = notifications.value.find(n => n.notification_id === id)
    if (item) item.is_read = true
  } catch (err: any) {
    console.error('标记已读失败:', err)
  }
}

const handleMarkAllRead = async () => {
  try {
    await markAllNotificationsRead()
    notifications.value.forEach(n => { n.is_read = true })
  } catch (err: any) {
    console.error('全部标记已读失败:', err)
  }
}

const changePage = (page: number) => {
  currentPage.value = page
  fetchNotifications()
}

const setFilter = (f: 'all' | 'unread' | 'read') => {
  filter.value = f
  currentPage.value = 1
  fetchNotifications()
}

const goBack = () => {
  router.push('/')
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchNotifications()
})
</script>

<template>
  <div class="list-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">消息通知</h1>
        <div class="header-buttons">
          <button @click="handleMarkAllRead" class="btn btn-primary" :disabled="loading">
            全部已读
          </button>
          <button @click="goBack" class="btn btn-back">返回首页</button>
        </div>
      </div>

      <div class="filter-tabs">
        <button :class="['tab', filter === 'all' ? 'active' : '']" @click="setFilter('all')">
          全部 ({{ total }})
        </button>
        <button :class="['tab', filter === 'unread' ? 'active' : '']" @click="setFilter('unread')">
          未读
        </button>
        <button :class="['tab', filter === 'read' ? 'active' : '']" @click="setFilter('read')">
          已读
        </button>
      </div>

      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else-if="error" class="error">
        <span>{{ error }}</span>
      </div>

      <div v-else-if="notifications.length === 0" class="empty-state">
        <span>暂无通知</span>
      </div>

      <div v-else class="notification-list">
        <div
          v-for="item in notifications"
          :key="item.notification_id"
          :class="['notification-item', { unread: !item.is_read }]"
          @click="!item.is_read && handleMarkRead(item.notification_id)"
        >
          <div class="notification-dot" v-if="!item.is_read"></div>
          <div class="notification-content">
            <div class="notification-title">{{ item.title }}</div>
            <div class="notification-body">{{ item.content }}</div>
            <div class="notification-time">{{ formatTime(item.created_at) }}</div>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="currentPage <= 1" @click="changePage(currentPage - 1)">上一页</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button :disabled="currentPage >= totalPages" @click="changePage(currentPage + 1)">下一页</button>
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

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing);
  border-bottom: 1px solid var(--border-light);
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

.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  font-size: var(--text-sm);
  border: none;
}

.btn-primary {
  background-color: var(--primary-500);
  color: white;
}

.btn-primary:hover { background-color: var(--primary-600); }

.btn-back {
  background-color: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
}

.btn-back:hover {
  background-color: var(--gray-200);
  color: var(--text-primary);
}

.filter-tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.tab {
  padding: 0.4rem 1rem;
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: all var(--transition);
}

.tab.active {
  background-color: var(--primary-500);
  color: white;
  border-color: var(--primary-500);
}

.loading, .error, .empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--text-secondary);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}

.error {
  color: var(--error);
  background-color: var(--error-light);
  border-color: #fca5a5;
}

.loading-spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid var(--border-light);
  border-top: 2px solid var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: var(--spacing-sm);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing);
  padding: var(--spacing);
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  cursor: default;
  transition: background-color var(--transition);
}

.notification-item.unread {
  background-color: var(--primary-50);
  border-color: var(--primary-200);
}

.notification-item.unread { cursor: pointer; }
.notification-item.unread:hover { background-color: var(--primary-100); }

.notification-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-500);
  margin-top: 6px;
  flex-shrink: 0;
}

.notification-content { flex: 1; }

.notification-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.notification-body {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.notification-time {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  opacity: 0.7;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing);
  margin-top: var(--spacing-lg);
  padding: var(--spacing);
}

.pagination button {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
}

.pagination button:disabled { opacity: 0.5; cursor: not-allowed; }

.pagination span { color: var(--text-secondary); font-size: var(--text-sm); }
</style>
