import { defineComponent, ref, computed } from '@vue-mini/core';
import { BASE_URL, startNotificationPolling, stopNotificationPolling, getUnreadCount, onUnreadChange } from '@/app';
import { requireAuth, logout } from '@/utils/auth';

export default defineComponent(() => {
  const userInfo = ref<any>(null);
  const studentCount = ref(0);
  const leaveCount = ref(0);
  const reviewerCount = ref(0);
  const teacherCount = ref(0);
  const courseCount = ref(0);
  const unreadCount = ref(0);

  // 角色显示名称映射 - 与 Web App 对齐
  const roleDisplayName = computed(() => {
    const roleMap: { [key: string]: string } = {
      'admin': '管理员',
      'teacher': '教师',
      'student': '学生',
      'reviewer': '审核员'
    };
    return roleMap[userInfo.value?.role] || '用户';
  });

  // 头像文字 - 处理 undefined 情况
  const avatarText = computed(() => {
    if (!userInfo.value?.name) return 'U';
    return userInfo.value.name.charAt(0).toUpperCase();
  });

  // 显示名称 - 处理 undefined 情况
  const displayName = computed(() => {
    return userInfo.value?.name || '用户';
  });

  // 获取各模块数量 - 与 Web App 对齐
  const getStudentCount = () => {
    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/students/count`,
      method: 'GET',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        studentCount.value = data?.students_count ?? data?.count ?? 0;
      }
    });
  };

  const getLeaveCount = () => {
    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/leaves/count`,
      method: 'GET',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        leaveCount.value = data?.leaves_count ?? data?.count ?? 0;
      }
    });
  };

  const getReviewerCount = () => {
    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/reviewers/count`,
      method: 'GET',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        reviewerCount.value = data?.reviewers_count ?? data?.count ?? 0;
      }
    });
  };

  const getTeacherCount = () => {
    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/teachers/count`,
      method: 'GET',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        teacherCount.value = data?.teachers_count ?? data?.count ?? 0;
      }
    });
  };

  const getCourseCount = () => {
    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/courses/count`,
      method: 'GET',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        courseCount.value = data?.courses_count ?? data?.count ?? 0;
      }
    });
  };

  // 刷新所有数据
  const refreshAllData = () => {
    getStudentCount();
    getLeaveCount();
    getReviewerCount();
    getTeacherCount();
    getCourseCount();
  };

  // 导航方法 - 与 Web App 对齐
  const goToStudents = () => {
    wx.navigateTo({
      url: '/pages/students/index'
    });
  };

  const goToLeaves = () => {
    wx.navigateTo({
      url: '/pages/leaves/index'
    });
  };

  const goToReviewers = () => {
    wx.navigateTo({
      url: '/pages/reviewers/index'
    });
  };

  const goToTeachers = () => {
    wx.navigateTo({
      url: '/pages/teachers/index'
    });
  };

  const goToCourses = () => {
    wx.navigateTo({
      url: '/pages/courses/index'
    });
  };

  const goToNotifications = () => {
    wx.navigateTo({
      url: '/pages/notifications/index'
    });
  };

  // 退出登录 - 与 Web App 对齐
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

  // 检查登录状态并获取数据
  const initializePage = async () => {
    const user = await requireAuth();
    if (user) {
      userInfo.value = user;
      refreshAllData();
    }
  };

  // 页面加载时获取数据
  const onReady = () => {
    // 使用 onShow 而不是 onReady 来避免重复初始化
    initializePage().catch((err) => {
      console.error('初始化失败:', err);
    });
  };

  // 页面显示时刷新数据
  const onShow = () => {
    const user = wx.getStorageSync('userInfo');
    if (user) {
      userInfo.value = user;
    }
    unreadCount.value = getUnreadCount() as number;
    onUnreadChange((count) => {
      unreadCount.value = count;
    });
    startNotificationPolling();
  };

  return {
    userInfo,
    roleDisplayName,
    avatarText,
    displayName,
    studentCount,
    leaveCount,
    reviewerCount,
    teacherCount,
    courseCount,
    unreadCount,
    goToStudents,
    goToLeaves,
    goToNotifications,
    goToReviewers,
    goToTeachers,
    goToCourses,
    handleLogout,
    onReady,
    onShow,
  };
});
