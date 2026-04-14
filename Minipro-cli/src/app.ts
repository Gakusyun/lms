import { createApp } from '@vue-mini/core';

// API Base URL - 便于部署时修改不同环境
export const BASE_URL = 'https://server.gxj62.cn/api/v1';
// 开发环境
// export const BASE_URL = 'http://localhost:8000/api/v1';

// 全局通知轮询
let _pollTimer: ReturnType<typeof setInterval> | null = null;
let _lastUnreadCount = 0;
let _onUnreadChange: ((count: number) => void) | null = null;

export const startNotificationPolling = () => {
  if (_pollTimer) return; // 已启动
  _pollTimer = setInterval(() => {
    const token = wx.getStorageSync('token');
    if (!token) { stopNotificationPolling(); return; }

    wx.request({
      url: `${BASE_URL}/notifications/unread-count`,
      method: 'GET',
      header: { Authorization: `Bearer ${token}` },
      success: (res: any) => {
        if (res.statusCode === 200 && res.data) {
          const count = res.data.unread_count ?? 0;
          if (count !== _lastUnreadCount) {
            _lastUnreadCount = count;
            // 设置 tabBar badge
            if (count > 0) {
              wx.setTabBarBadge({ index: 0, text: count > 99 ? '99+' : String(count) });
            } else {
              wx.removeTabBarBadge({ index: 0 });
            }
            // 回调通知
            _onUnreadChange?.(count);
          }
        }
      },
      fail: () => { /* 静默失败 */ },
    });
  }, 15000); // 每15秒轮询一次
};

export const stopNotificationPolling = () => {
  if (_pollTimer) {
    clearInterval(_pollTimer);
    _pollTimer = null;
  }
  wx.removeTabBarBadge({ index: 0 });
};

export const getUnreadCount = () => _lastUnreadCount;

export const onUnreadChange = (cb: (count: number) => void) => {
  _onUnreadChange = cb;
};

createApp(() => {
});
