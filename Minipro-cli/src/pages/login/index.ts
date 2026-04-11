import { defineComponent, ref } from '@vue-mini/core';
import { BASE_URL } from '@/app';

interface LoginFormData {
  id: string;
  password: string;
}

interface UserInfo {
  role: string;
  id: string;
  name: string;
}

export default defineComponent(() => {
  const loginForm = ref<LoginFormData>({
    id: '',
    password: ''
  });

  const loading = ref(false);
  const errorMessage = ref('');

  // 检查是否已经登录 - 与Web App对齐
  const checkAlreadyLoggedIn = () => {
    const token = wx.getStorageSync('token');

    if (token) {
      // 已经有token，直接跳转到主页（token有效性由主页requireAuth验证）
      wx.switchTab({
        url: '/pages/home/index'
      });
      return true;
    }
    return false;
  };

  // 页面加载时检查登录状态
  const onLoad = () => {
    if (checkAlreadyLoggedIn()) {
      return;
    }
  };

  // 存储登录信息到本地 - 与 Web App 对齐
  const storeLoginInfo = (token: string, role: string, id: string, name: string) => {
    wx.setStorageSync('token', token);
    wx.setStorageSync('role', role);
    wx.setStorageSync('id', id);
    wx.setStorageSync('name', name);

    // 同时存储 userInfo，保持兼容性
    wx.setStorageSync('userInfo', {
      role,
      id,
      name
    } as UserInfo);
  };

  // 登录请求 - 与 Web App 逻辑对齐
  const handleLogin = async () => {
    try {
      loading.value = true;
      errorMessage.value = ''; // 清空错误信息

      // 验证表单 - 与 Web App 对齐
      if (!loginForm.value.id || !loginForm.value.password) {
        errorMessage.value = '请填写完整的账号和密码';
        return;
      }

      // 不生成token，让后端返回JWT token - 与Web App对齐
      const requestData = {
        id: parseInt(loginForm.value.id) || loginForm.value.id,
        password: loginForm.value.password
      };

      console.log('发送登录请求:', `${BASE_URL}/login`);
      console.log('请求数据:', requestData);

      wx.request({
        url: `${BASE_URL}/login`,
        method: 'POST',
        header: {
          'content-type': 'application/json'
        },
        data: requestData,
        success: (res) => {
          console.log('登录响应:', res);
          if (res.statusCode === 200 && res.data && typeof res.data === 'object') {
            // 登录成功，使用后端返回的JWT token - 与Web App对齐
            const response = res.data as any;

            // 存储登录信息 - 与 Web App 对齐
            storeLoginInfo(
              response.token || '', // ✅ 使用后端返回的JWT token
              response.role || '',
              (response.id || loginForm.value.id).toString(),
              response.name || ''
            );

            console.log('登录成功:', response);

            // 立即跳转到主页 - 与 Web App 对齐
            wx.switchTab({
              url: '/pages/home/index'
            });
          } else {
            console.error('登录响应异常:', res);
            // 使用统一的错误提示 - 与 Web App 对齐
            const responseData = res.data as any;
            errorMessage.value = responseData?.message || '登录失败，请检查用户名和密码';
          }
        },
        fail: (err) => {
          console.error('登录请求失败:', err);
          // 使用统一的错误提示 - 与 Web App 对齐
          errorMessage.value = '网络错误，请检查网络连接后重试';
        },
        complete: () => {
          loading.value = false;
        }
      });
    } catch (error) {
      console.error('登录异常:', error);
      loading.value = false;
      // 使用统一的错误提示 - 与 Web App 对齐
      errorMessage.value = '登录异常，请重试';
    }
  };

  // 处理账号输入
  const onIdInput = (e: any) => {
    loginForm.value.id = e.detail.value;
    errorMessage.value = ''; // 输入时清空错误信息
  };

  // 处理密码输入
  const onPasswordInput = (e: any) => {
    loginForm.value.password = e.detail.value;
    errorMessage.value = ''; // 输入时清空错误信息
  };

  return {
    loginForm,
    loading,
    errorMessage,
    handleLogin,
    onIdInput,
    onPasswordInput,
    onLoad
  };
});