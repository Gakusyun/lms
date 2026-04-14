import { defineComponent, ref, reactive } from '@vue-mini/core';
import { BASE_URL } from '@/app';
import { requireAuth } from '@/utils/auth';

interface Leave {
  leave_id: number;
  student_id: number;
  student_name?: string;
  leave_type: string;
  leave_hours: string;
  leave_date: string;
  status: string;
  reviewer_id: number;
  reviewer_name?: string;
  audit_remarks?: string;
  remarks?: string;
  materials?: string;
  course_id?: number;
  teacher_id?: number;
  leave_date_formatted?: string;
}

interface Course {
  course_id: number;
  course_name: string;
  teacher_id: number;
  teacher_name: string;
}

export default defineComponent(() => {
  const leaves = ref<Leave[]>([]);
  const loading = ref(false);
  const page = ref(1);
  const pageSize = 20;
  const total = ref(0);
  const totalPages = ref(0);
  const userInfo = ref<any>(null);

  // 创建请假条相关状态
  const showCreateModal = ref(false);
  const isCreating = ref(false);
  const createError = ref('');
  const courses = ref<Course[]>([]);
  const courseOptions = ref<{ label: string, value: number }[]>([]);
  const selectedCourseIndex = ref(-1);

  // 创建请假条表单数据
  const leaveForm = reactive({
    student_id: 0,
    leave_date: '',
    leave_hours: '',
    leave_type: '',
    course_id: 0,
    teacher_id: 0,
    remarks: '',
    materials: '',
    status: '待审批'
  });

  // 格式化日期显示
  const formatDate = (dateStr: string): string => {
    if (!dateStr) return '';

    // 解析ISO日期字符串
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr; // 如果解析失败，返回原始字符串

    const now = new Date();
    const currentYear = now.getFullYear();
    const dateYear = date.getFullYear();

    if (dateYear === currentYear) {
      // 本年只显示月日
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${month}-${day}`;
    } else {
      // 非本年显示年月日
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${year}-${month}-${day}`;
    }
  };

  // 获取请假数据
  const fetchLeaves = (isRefresh = false) => {
    if (isRefresh) {
      page.value = 1;
      leaves.value = [];
    }

    loading.value = true;
    wx.showLoading({
      title: '加载中...',
    });

    const token = wx.getStorageSync('token');
    // 统一使用 /leaves 端点，后端会根据 token 中的角色自动过滤数据并注入关联字段
    const url = BASE_URL + '/leaves';

    wx.request({
      url: url,
      method: 'GET',
      data: {
        page: page.value,
        page_size: pageSize
      },
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        console.log('请假API返回数据:', res.data);
        const data = res.data as any;

        // 处理分页响应格式
        let leavesData = [];
        if (data && data.items && Array.isArray(data.items)) {
          // 新的分页格式: {items: [...], total: X, page: Y, page_size: Z, total_pages: W}
          leavesData = data.items;
          total.value = data.total || 0;
          totalPages.value = data.total_pages || 0;
        } else if (data && Array.isArray(data)) {
          // 直接返回数组（向后兼容）
          leavesData = data;
        } else if (data && data.list && Array.isArray(data.list)) {
          // 返回包含list的对象（向后兼容）
          leavesData = data.list;
        } else if (data && typeof data === 'object' && !Array.isArray(data)) {
          // 返回单个对象，包装成数组（向后兼容）
          leavesData = [data];
        }

        console.log('处理后的请假数据:', leavesData);
        console.log('分页信息:', { page: page.value, total: total.value, totalPages: totalPages.value });

        // 格式化日期字段
        const formattedLeavesData = leavesData.map((leave: any) => ({
          ...leave,
          leave_date_formatted: formatDate(leave.leave_date)
        }));

        if (isRefresh) {
          leaves.value = formattedLeavesData;
        } else {
          leaves.value = [...leaves.value, ...formattedLeavesData];
        }
        wx.stopPullDownRefresh();
      },
      fail: (error) => {
        console.error('获取请假数据失败:', error);
        wx.showToast({
          title: '加载失败',
          icon: 'error'
        });
        wx.stopPullDownRefresh();
      },
      complete: () => {
        loading.value = false;
        wx.hideLoading();
      }
    });
  };

  // 加载更多数据
  const loadMore = () => {
    if (!loading.value) {
      // 检查是否还有更多页面
      if (totalPages.value === 0 || page.value < totalPages.value) {
        page.value++;
        fetchLeaves();
      } else {
        console.log('没有更多数据了');
      }
    }
  };


  // 下拉刷新
  const onPullDownRefresh = () => {
    fetchLeaves(true);
  };

  // 获取课程数据
  const fetchCourses = async () => {
    try {
      const token = wx.getStorageSync('token');
      wx.request({
        url: `${BASE_URL}/courses`,
        method: 'GET',
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          console.log('课程API返回数据:', res.data);
          const data = res.data as any;

          let coursesData = [];
          if (data && data.items && Array.isArray(data.items)) {
            coursesData = data.items;
          } else if (data && Array.isArray(data)) {
            coursesData = data;
          }

          courses.value = coursesData;
          courseOptions.value = [
            { label: '请选择课程', value: 0 },
            ...coursesData.map((course: Course) => ({
              label: `${course.course_name} - ${course.teacher_name}`,
              value: course.course_id
            }))
          ];
        },
        fail: (error) => {
          console.error('获取课程失败:', error);
        }
      });
    } catch (error) {
      console.error('获取课程失败:', error);
    }
  };

  // 打开创建弹窗
  const openCreateModal = async () => {
    showCreateModal.value = true;
    createError.value = '';

    // 获取课程数据
    await fetchCourses();

    // 获取当前用户信息
    const userInfo = wx.getStorageSync('userInfo');
    if (userInfo) {
      leaveForm.student_id = parseInt(userInfo.id);
    }

    // 重置表单
    Object.assign(leaveForm, {
      student_id: userInfo ? parseInt(userInfo.id) : 0,
      leave_date: '',
      leave_hours: '',
      leave_type: '',
      course_id: 0,
      teacher_id: 0,
      remarks: '',
      materials: '',
      status: '待审批'
    });

    selectedCourseIndex.value = 0;
  };

  // 关闭创建弹窗
  const closeCreateModal = () => {
    showCreateModal.value = false;
    createError.value = '';
  };

  // 表单输入处理
  const onStudentIdInput = (e: any) => {
    leaveForm.student_id = parseInt(e.detail.value) || 0;
  };

  const onDateChange = (e: any) => {
    leaveForm.leave_date = e.detail.value;
  };

  const onLeaveHoursInput = (e: any) => {
    leaveForm.leave_hours = e.detail.value;
  };

  const onLeaveTypeInput = (e: any) => {
    leaveForm.leave_type = e.detail.value;
  };

  const onRemarksInput = (e: any) => {
    leaveForm.remarks = e.detail.value;
  };

  const onCourseChange = (e: any) => {
    selectedCourseIndex.value = e.detail.value;
    if (e.detail.value > 0) {
      const selectedCourse = courses.value.find(c => c.course_id === courseOptions.value[e.detail.value].value);
      if (selectedCourse) {
        leaveForm.course_id = selectedCourse.course_id;
        leaveForm.teacher_id = selectedCourse.teacher_id;
      }
    } else {
      leaveForm.course_id = 0;
      leaveForm.teacher_id = 0;
    }
  };

  // 创建请假条
  const handleCreateLeave = async () => {
    try {
      isCreating.value = true;
      createError.value = '';

      // 验证必填字段
      if (!leaveForm.student_id || !leaveForm.leave_date || !leaveForm.leave_hours) {
        createError.value = '请填写必填字段：学生ID、请假日期、请假课时';
        return;
      }

      const token = wx.getStorageSync('token');
      const formattedData: any = {
        student_id: leaveForm.student_id,
        leave_date: leaveForm.leave_date,
        leave_hours: leaveForm.leave_hours,
        status: leaveForm.status
      };

      // 添加可选字段
      if (leaveForm.leave_type) {
        formattedData.leave_type = leaveForm.leave_type.slice(0, 8);
      }
      if (leaveForm.remarks) {
        formattedData.remarks = leaveForm.remarks.slice(0, 100);
      }
      if (leaveForm.course_id > 0) {
        formattedData.course_id = leaveForm.course_id;
        formattedData.teacher_id = leaveForm.teacher_id;
      }

      console.log('提交请假条数据:', formattedData);

      wx.request({
        url: `${BASE_URL}/leaves`,
        method: 'POST',
        data: formattedData,
        header: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          console.log('创建请假条成功:', res);
          wx.showToast({
            title: '创建成功',
            icon: 'success'
          });
          closeCreateModal();
          fetchLeaves(true);
        },
        fail: (error: any) => {
          console.error('创建请假条失败:', error);
          let errorMessage = '创建失败，请重试';
          if (error && error.response && error.response.data) {
            const errorData = error.response.data;
            if (errorData.detail && Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map((item: any) => `${item.loc?.join('.')}: ${item.msg}`).join('; ');
            } else if (errorData.message) {
              errorMessage = errorData.message;
            }
          }
          createError.value = errorMessage;
          wx.showToast({
            title: errorMessage,
            icon: 'error'
          });
        },
        complete: () => {
          isCreating.value = false;
        }
      });
    } catch (error) {
      console.error('创建请假条失败:', error);
      createError.value = '创建失败，请重试';
      isCreating.value = false;
    }
  };

  // 审核请假条 - 使用与 Web App 相同的 API 端点
  const auditLeave = (e: any) => {
    const { id, status } = e.currentTarget.dataset;
    const leave = leaves.value.find(l => l.leave_id === id);

    if (!leave) return;

    // 审核状态映射
    const statusMap: { [key: string]: string } = {
      'approve': '已批准',
      'reject': '已拒绝'
    };

    const auditStatus = statusMap[status];
    if (!auditStatus) return;

    wx.showModal({
      title: `确认${auditStatus === '已批准' ? '通过' : '拒绝'}`,
      editable: true,
      placeholderText: '请输入审核意见（可选）',
      success: (res) => {
        if (res.confirm) {
          const token = wx.getStorageSync('token');
          const remarks = res.content || '';

          // 使用专用 approve/reject 端点
          const endpoint = auditStatus === '已批准'
            ? `${BASE_URL}/leaves/approve/${id}?audit_remarks=${encodeURIComponent(remarks)}`
            : `${BASE_URL}/leaves/reject/${id}?audit_remarks=${encodeURIComponent(remarks)}`;

          wx.request({
            url: endpoint,
            method: 'POST',
            header: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            success: () => {
              wx.showToast({
                title: '审核成功',
                icon: 'success'
              });
              fetchLeaves(true);
            },
            fail: (error) => {
              console.error('审核失败:', error);
              wx.showToast({
                title: '审核失败',
                icon: 'error'
              });
            }
          });
        }
      }
    });
  };

  // 审核请假条（保留原方法兼容旧代码）
  const approveLeave = (e: any) => {
    auditLeave({ currentTarget: { dataset: { id: e.currentTarget.dataset.id, status: 'approve' } } });
  };

  const rejectLeave = (e: any) => {
    auditLeave({ currentTarget: { dataset: { id: e.currentTarget.dataset.id, status: 'reject' } } });
  };

  // 返回上一页
  const goBack = () => {
    wx.navigateBack();
  };

  // 检查登录状态并获取数据
  const initializePage = async () => {
    const user = await requireAuth();
    if (user) {
      userInfo.value = user;
      console.log('页面加载完成，自动获取数据');
      fetchLeaves(true);
    }
  };

  // 页面加载时获取数据
  const onReady = () => {
    initializePage();
  };

  return {
    leaves,
    loading,
    total,
    totalPages,
    page,
    showCreateModal,
    isCreating,
    createError,
    leaveForm,
    courses,
    courseOptions,
    selectedCourseIndex,
    userInfo,
    fetchLeaves,
    loadMore,
    onPullDownRefresh,
    goBack,
    onReady,
    openCreateModal,
    closeCreateModal,
    onStudentIdInput,
    onDateChange,
    onLeaveHoursInput,
    onLeaveTypeInput,
    onRemarksInput,
    onCourseChange,
    handleCreateLeave,
    approveLeave,
    rejectLeave
  };
});