import { BASE_URL } from '@/app';

// 统一的 API 请求函数
export const request = (options: {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  data?: any;
  header?: any;
}) => {
  const token = wx.getStorageSync('token');

  // 默认配置 - 仅使用 Authorization Header 传递 token
  const defaultOptions = {
    url: `${BASE_URL}${options.url}`,
    method: options.method || 'GET',
    data: options.data,
    header: {
      'content-type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      ...options.header
    }
  };

  return new Promise((resolve, reject) => {
    wx.request({
      ...defaultOptions,
      success: (res) => {
        // 处理响应状态码
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          // 处理错误状态码
          let message = '请求失败，请稍后再试';
          if (res.data && typeof res.data === 'object' && 'detail' in res.data) {
            message = res.data.detail;
          }

          // 处理401未授权错误
          if (res.statusCode === 401) {
            // 清除本地存储的token
            wx.removeStorageSync('token');
            wx.removeStorageSync('userInfo');
            // 跳转到登录页
            wx.redirectTo({ url: '/pages/login/index' });
          }

          // 显示错误消息
          wx.showToast({
            title: message,
            icon: 'error',
            duration: 2000
          });

          reject({ statusCode: res.statusCode, message });
        }
      },
      fail: (error) => {
        console.error('请求失败:', error);

        // 处理网络错误
        wx.showToast({
          title: '网络错误，请检查网络连接',
          icon: 'error',
          duration: 2000
        });

        reject(error);
      }
    });
  });
};