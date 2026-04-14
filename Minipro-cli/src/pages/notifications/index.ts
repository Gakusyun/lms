import { defineComponent, ref, onUnmounted } from '@vue-mini/core';
import { BASE_URL, startNotificationPolling, stopNotificationPolling, getUnreadCount, onUnreadChange } from '@/app';
import { requireAuth } from '@/utils/auth';

interface NotificationItem {
  notification_id: number;
  title: string;
  content: string;
  type: string;
  is_read: boolean;
  related_type?: string;
  related_id?: number;
  created_at: string;
}

export default defineComponent(() => {
  const notifications = ref<NotificationItem[]>([]);
  const loading = ref(false);
  const page = ref(1);
  const pageSize = 20;
  const totalPages = ref(0);
  const userInfo = ref<any>(null);

  // 获取通知列表
  const fetchNotifications = (isRefresh = false) => {
    if (isRefresh) {
      page.value = 1;
      notifications.value = [];
    }

    loading.value = true;
    const token = wx.getStorageSync('token');

    wx.request({
      url: `${BASE_URL}/notifications`,
      method: 'GET',
      data: { page: page.value, page_size: pageSize },
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        let items: NotificationItem[] = [];
        if (data?.items && Array.isArray(data.items)) {
          items = data.items;
          totalPages.value = data.total_pages || 0;
        } else if (Array.isArray(data)) {
          items = data;
        }

        if (isRefresh) {
          notifications.value = items;
        } else {
          notifications.value = [...notifications.value, ...items];
        }
        wx.stopPullDownRefresh();
      },
      fail: () => {
        wx.showToast({ title: '加载失败', icon: 'error' });
        wx.stopPullDownRefresh();
      },
      complete: () => {
        loading.value = false;
      },
    });
  };

  // 加载更多
  const loadMore = () => {
    if (!loading.value && (totalPages.value === 0 || page.value < totalPages.value)) {
      page.value++;
      fetchNotifications();
    }
  };

  // 下拉刷新
  const onPullDownRefresh = () => {
    fetchNotifications(true);
  };

  // 标记单条已读
  const markAsRead = (e: any) => {
    const { id } = e.currentTarget.dataset;
    const item = notifications.value.find((n) => n.notification_id === id);
    if (!item || item.is_read) return;

    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/notifications/${id}/read`,
      method: 'POST',
      header: { Authorization: `Bearer ${token}` },
      success: () => {
        item.is_read = true;
      },
    });
  };

  // 全部标记已读
  const markAllRead = () => {
    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/notifications/read-all`,
      method: 'POST',
      header: { Authorization: `Bearer ${token}` },
      success: () => {
        notifications.value.forEach((n) => { n.is_read = true; });
        wx.showToast({ title: '已全部标记已读', icon: 'success' });
      },
    });
  };

  // 格式化时间
  const formatTime = (dateStr: string): string => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    const m = date.getMonth() + 1;
    const d = date.getDate();
    if (date.getFullYear() === now.getFullYear()) {
      return `${m}-${d}`;
    }
    return `${date.getFullYear()}-${m}-${d}`;
  };

  // 类型图标映射
  const typeIcon = (type: string): string => {
    const map: Record<string, string> = {
      success: '✅',
      warning: '⚠️',
      error: '❌',
      info: 'ℹ️',
    };
    return map[type] || '📢';
  };

  // 返回
  const goBack = () => {
    wx.navigateBack();
  };

  // 初始化
  const onReady = async () => {
    const user = await requireAuth();
    if (user) {
      userInfo.value = user;
      fetchNotifications(true);
    }
  };

  return {
    notifications,
    loading,
    page,
    totalPages,
    userInfo,
    fetchNotifications,
    loadMore,
    onPullDownRefresh,
    markAsRead,
    markAllRead,
    formatTime,
    typeIcon,
    goBack,
    onReady,
  };
});
