import { request } from './request';

export interface UserInfo {
  role: string;
  id: string;
  name: string;
}

// 检查登录状态 - 与Web App对齐的同步验证逻辑
export const checkLoginStatus = (): Promise<{ success: boolean; userInfo?: UserInfo }> => {
  return new Promise((resolve) => {
    const token = wx.getStorageSync('token');

    // 如果没有token，立即返回失败
    if (!token) {
      resolve({ success: false });
      return;
    }

    // 使用封装好的request函数，自动添加token到params和headers
    request({
      url: '/login/check',
      method: 'GET'
    }).then((res) => {
      if (res && typeof res === 'object' && !Array.isArray(res)) {
        // token有效，更新本地用户信息
        const userInfo: UserInfo = {
          role: (res as Record<string, any>).role || '',
          id: (res as Record<string, any>).id?.toString() || '',
          name: (res as Record<string, any>).name || ''
        };

        // 同步存储所有用户信息
        wx.setStorageSync('userInfo', userInfo);
        wx.setStorageSync('role', userInfo.role);
        wx.setStorageSync('id', userInfo.id);
        wx.setStorageSync('name', userInfo.name);

        resolve({ success: true, userInfo });
      } else {
        // token无效，清除本地存储
        console.warn('Token验证失败，清除本地存储');
        wx.removeStorageSync('token');
        wx.removeStorageSync('userInfo');
        wx.removeStorageSync('role');
        wx.removeStorageSync('id');
        wx.removeStorageSync('name');
        resolve({ success: false });
      }
    }).catch((err) => {
      console.error('Token验证请求失败:', err);
      // 网络失败时清除本地存储，要求重新登录
      wx.removeStorageSync('token');
      wx.removeStorageSync('userInfo');
      wx.removeStorageSync('role');
      wx.removeStorageSync('id');
      wx.removeStorageSync('name');
      resolve({ success: false });
    });
  });
};

// 获取本地用户信息
export const getLocalUserInfo = (): UserInfo | null => {
  return wx.getStorageSync('userInfo') || null;
};

// 检查是否需要登录
export const requireAuth = async () => {
  const { success, userInfo } = await checkLoginStatus();

  if (!success) {
    // 统一使用reLaunch跳转到登录页
    wx.reLaunch({
      url: '/pages/login/index'
    });
    return false;
  }

  return userInfo;
};

// 退出登录
export const logout = async () => {
  const token = wx.getStorageSync('token');

  if (token) {
    // 使用封装好的request函数调用退出登录API
    request({
      url: '/logout',
      method: 'POST'
    }).then(() => {
      // 清除本地存储
      clearAuthData();
      wx.reLaunch({
        url: '/pages/login/index'
      });
    }).catch(() => {
      // 即使API调用失败，也清除本地存储
      clearAuthData();
      wx.reLaunch({
        url: '/pages/login/index'
      });
    });
  } else {
    // 没有token直接清除并跳转登录页
    clearAuthData();
    wx.reLaunch({
      url: '/pages/login/index'
    });
  }
};

// 清除认证数据
const clearAuthData = () => {
  wx.removeStorageSync('token');
  wx.removeStorageSync('userInfo');
  wx.removeStorageSync('role');
  wx.removeStorageSync('id');
  wx.removeStorageSync('name');
};
