import { defineComponent, ref, reactive } from '@vue-mini/core';
import { UserInfo, requireAuth, logout, getLocalUserInfo } from '@/utils/auth';
import { BASE_URL, startNotificationPolling, getUnreadCount } from '@/app';

defineComponent(() => {
  const userInfo = ref<UserInfo | null>(null);
  const loading = ref(true);

  // 修改密码相关状态
  const showChangePassword = ref(false);
  const isChangingPassword = ref(false);
  const passwordError = ref('');

  // 扫码登录相关状态
  const qrChecking = ref(false);
  const qrErrorMessage = ref('');

  // 修改密码表单数据
  const passwordForm = reactive({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });

  // 加载用户信息 - 与Web App对齐（只读本地存储，不验证token）
  const loadUserInfo = () => {
    try {
      // 直接从本地存储读取用户信息，不调用API
      const id = wx.getStorageSync('id');
      const name = wx.getStorageSync('name');
      const role = wx.getStorageSync('role');

      if (id && name && role) {
        userInfo.value = { id, name, role };
      }
    } catch (error) {
      console.error('加载用户信息失败:', error);
    } finally {
      loading.value = false;
    }
  };

  // 刷新本地用户信息（不验证token）
  const refreshLocalUserInfo = () => {
    const localUser = getLocalUserInfo();
    if (localUser) {
      userInfo.value = localUser;
    }
  };

  // 退出登录
  const handleLogout = () => {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          logout();
        }
      }
    });
  };

  // 页面显示时刷新本地用户信息（不重复验证token）
  const onShow = () => {
    refreshLocalUserInfo();
    startNotificationPolling();
  };

  // 显示修改密码模态框
  const showChangePasswordModal = () => {
    showChangePassword.value = true;
    passwordError.value = '';
  };

  // 隐藏修改密码模态框
  const hideChangePasswordModal = () => {
    showChangePassword.value = false;
    passwordForm.old_password = '';
    passwordForm.new_password = '';
    passwordForm.confirm_password = '';
    passwordError.value = '';
  };

  // 处理原密码输入
  const onOldPasswordInput = (e: any) => {
    passwordForm.old_password = e.detail.value;
  };

  // 处理新密码输入
  const onNewPasswordInput = (e: any) => {
    passwordForm.new_password = e.detail.value;
  };

  // 处理确认密码输入
  const onConfirmPasswordInput = (e: any) => {
    passwordForm.confirm_password = e.detail.value;
  };

  // 处理修改密码
  const handleChangePassword = async () => {
    if (!passwordForm.old_password || !passwordForm.new_password || !passwordForm.confirm_password) {
      passwordError.value = '请填写完整信息';
      return;
    }

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      passwordError.value = '两次输入的新密码不一致';
      return;
    }

    if (passwordForm.new_password.length < 6) {
      passwordError.value = '新密码长度不能少于6位';
      return;
    }

    isChangingPassword.value = true;
    passwordError.value = '';

    try {
      const token = wx.getStorageSync('token');
      
      wx.request({
        url: `${BASE_URL}/change-password`,
        method: 'POST',
        data: {
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password
        },
        header: {
          'content-type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            wx.showToast({
              title: '密码修改成功',
              icon: 'success'
            });
            hideChangePasswordModal();
          } else {
            passwordError.value = '密码修改失败，请检查原密码是否正确';
          }
        },
        fail: (error) => {
          console.error('修改密码失败:', error);
          passwordError.value = '网络错误，请重试';
        },
        complete: () => {
          isChangingPassword.value = false;
        }
      });
    } catch (error) {
      console.error('修改密码异常:', error);
      passwordError.value = '修改失败，请重试';
      isChangingPassword.value = false;
    }
  };

  // 页面加载时检查登录状态
  const onLoad = () => {
    loadUserInfo();
  };

  // 处理扫码登录 - 扫描Web App的二维码
  const handleScanQRCode = () => {
    qrChecking.value = true;
    qrErrorMessage.value = '';

    // 调用微信扫码API
    wx.scanCode({
      onlyFromCamera: false,
      scanType: ['qrCode'],
      success: (res) => {
        console.log('扫码成功:', res);

        // 获取二维码中的token（Web App的token）
        const scannedToken = res.result;

        if (!scannedToken) {
          qrErrorMessage.value = '二维码无效，请重试';
          qrChecking.value = false;
          return;
        }

        // 调用后端API验证扫码登录
        wx.request({
          url: `${BASE_URL}/login/orcode`,
          method: 'GET',
          data: {
            login_token: scannedToken
          },
          header: {
            'Authorization': `Bearer ${wx.getStorageSync('token')}`
          },
          success: (loginRes) => {
            if (loginRes.statusCode === 200) {
              console.log('扫码登录成功:', loginRes.data);
              wx.showToast({
                title: 'Web App登录成功',
                icon: 'success'
              });
            } else {
              console.error('扫码登录验证失败:', loginRes);
              qrErrorMessage.value = '登录验证失败，请确认二维码是否正确';
            }
          },
          fail: (err) => {
            console.error('扫码登录请求失败:', err);
            qrErrorMessage.value = '网络错误，请重试';
          },
          complete: () => {
            qrChecking.value = false;
            // 3秒后清除错误提示
            if (qrErrorMessage.value) {
              setTimeout(() => {
                qrErrorMessage.value = '';
              }, 3000);
            }
          }
        });
      },
      fail: (err) => {
        console.error('扫码失败:', err);
        qrErrorMessage.value = '扫码失败，请重试';
        qrChecking.value = false;
        // 3秒后清除错误提示
        setTimeout(() => {
          qrErrorMessage.value = '';
        }, 3000);
      }
    });
  };

  // 返回首页 - 与 Web App 对齐
  const goHome = () => {
    wx.switchTab({
      url: '/pages/home/index'
    });
  };

  // 跳转到通知页面
  const goToNotifications = () => {
    wx.navigateTo({
      url: '/pages/notifications/index'
    });
  };

  return {
    userInfo,
    loading,
    showChangePassword,
    isChangingPassword,
    passwordError,
    passwordForm,
    qrChecking,
    qrErrorMessage,
    handleLogout,
    onShow,
    onLoad,
    showChangePasswordModal,
    hideChangePasswordModal,
    onOldPasswordInput,
    onNewPasswordInput,
    onConfirmPasswordInput,
    handleChangePassword,
    handleScanQRCode,
    goHome,
    goToNotifications,
  };
});