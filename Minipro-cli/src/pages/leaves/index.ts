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
  qr_code?: string;
  qr_valid_from?: string;
  qr_valid_until?: string;
  qr_use_count?: number;
  qr_max_uses?: number;
  guarantee_student_id?: number;
  guarantee_student_name?: string;
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
  const leaveTypeOptions = ['事假', '病假', '公假', '婚假', '丧假', '其他'];
  const selectedLeaveTypeIndex = ref(-1);

  // 创建请假条表单数据
  const leaveForm = reactive({
    student_id: 0,
    guarantee_student_id: 0,
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

  const onLeaveTypeChange = (e: any) => {
    selectedLeaveTypeIndex.value = e.detail.value;
    leaveForm.leave_type = leaveTypeOptions[e.detail.value] || '';
  };

  const onGuaranteeStudentIdInput = (e: any) => {
    leaveForm.guarantee_student_id = parseInt(e.detail.value) || 0;
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
      if (leaveForm.guarantee_student_id > 0) {
        formattedData.guarantee_student_id = leaveForm.guarantee_student_id;
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
    console.log('auditLeave called', e);
    console.log('currentTarget.dataset:', e.currentTarget?.dataset);
    const { id, status } = e.currentTarget.dataset;
    console.log('parsed id:', id, 'status:', status);
    const leave = leaves.value.find(l => l.leave_id === id);

    if (!leave) {
      console.log('leave not found for id:', id);
      return;
    }

    // 审核状态映射
    const statusMap: { [key: string]: string } = {
      'approve': '已批准',
      'reject': '已拒绝'
    };

    const auditStatus = statusMap[status];
    console.log('auditStatus:', auditStatus);
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

  // 担保请假条
  const guaranteeLeave = (e: any) => {
    const { id } = e.currentTarget.dataset;
    const leave = leaves.value.find(l => l.leave_id === id);
    if (!leave) return;

    wx.showModal({
      title: '确认担保',
      content: `确定要担保这张请假条吗？\n学生: ${leave.student_name || '-'}\n类型: ${leave.leave_type}\n课时: ${leave.leave_hours}`,
      success: (res) => {
        if (res.confirm) {
          const token = wx.getStorageSync('token');
          wx.request({
            url: `${BASE_URL}/leaves/guarantee/${id}`,
            method: 'POST',
            header: {
              'Authorization': `Bearer ${token}`
            },
            success: () => {
              wx.showToast({
                title: '担保成功',
                icon: 'success'
              });
              fetchLeaves(true);
            },
            fail: (error: any) => {
              console.error('担保失败:', error);
              wx.showToast({
                title: (error?.response?.data?.detail) || '担保失败',
                icon: 'error'
              });
            }
          });
        }
      }
    });
  };

  // 判断是否为该学生的担保人
  const isGuarantorFor = (leave: Leave): boolean => {
    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo) return false;
    return leave.guarantee_student_id === parseInt(userInfo.id) && leave.student_id !== parseInt(userInfo.id);
  };

  // 销假 - 辅导员确认学生已返校报到
  const closeOffLeave = (e: any) => {
    const { id } = e.currentTarget.dataset;
    const leave = leaves.value.find(l => l.leave_id === id);
    if (!leave) return;

    wx.showModal({
      title: '确认销假',
      content: `确定要对该请假执行销假操作吗？\n学生: ${leave.student_name || '-'}\n类型: ${leave.leave_type || '-'}\n课时: ${leave.leave_hours || '-'}`
    }).then((res: any) => {
      if (res.confirm) {
        const token = wx.getStorageSync('token');
        wx.request({
          url: `${BASE_URL}/leaves/close-off/${id}`,
          method: 'POST',
          header: {
            'Authorization': `Bearer ${token}`
          },
          success: () => {
            wx.showToast({ title: '销假成功', icon: 'success' });
            fetchLeaves(true);
          },
          fail: (error: any) => {
            console.error('销假失败:', error);
            wx.showToast({
              title: (error?.response?.data?.detail) || '销假失败',
              icon: 'error'
            });
          }
        });
      }
    });
  };

  // 判断是否可以销假（辅导员/管理员可以对已批准的请假执行销假）
  const canCloseOff = (leave: Leave): boolean => {
    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo) return false;
    return leave.status === '已批准' && (userInfo.role === 'reviewer' || userInfo.role === 'admin');
  };

  // 返回上一页
  const goBack = () => {
    wx.navigateBack();
  };

  // ===== 二维码凭证展示 =====
  const showQRModal = ref(false);
  const qrLeaveItem = ref<Leave | null>(null);
  const qrCodeBase64 = ref('');
  const qrLoading = ref(false);
  const qrError = ref('');
  const qrValidInfo = ref<{ from: string; until: string; used: number; max: number }>({ from: '', until: '', used: 0, max: 0 });

  // 点击查看请假二维码凭证
  const showLeaveQR = (e: any) => {
    const { id } = e.currentTarget.dataset;
    const leave = leaves.value.find((l) => l.leave_id === id);
    if (!leave) return;

    if (leave.status !== '已批准') {
      wx.showToast({ title: '仅已批准的请假可查看凭证', icon: 'none' });
      return;
    }

    // 如果列表数据中已有 qr_code，直接展示
    if (leave.qr_code) {
      qrLeaveItem.value = leave;
      qrCodeBase64.value = leave.qr_code;
      qrValidInfo.value = {
        from: leave.qr_valid_from || '',
        until: leave.qr_valid_until || '',
        used: leave.qr_use_count || 0,
        max: leave.qr_max_uses || 1,
      };
      showQRModal.value = true;
      return;
    }

    // 否则请求后端获取
    qrLoading.value = true;
    qrError.value = '';
    qrLeaveItem.value = leave;
    showQRModal.value = true;

    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/leaves/${id}/qr`,
      method: 'GET',
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        if (data && data.qr_code) {
          qrCodeBase64.value = data.qr_code;
          qrValidInfo.value = {
            from: data.qr_valid_from || '',
            until: data.qr_valid_until || '',
            used: data.qr_use_count || 0,
            max: data.qr_max_uses || 1,
          };
        } else {
          qrError.value = '未找到请假凭证二维码';
        }
      },
      fail: () => {
        qrError.value = '获取二维码失败';
      },
      complete: () => {
        qrLoading.value = false;
      },
    });
  };

  // 关闭二维码弹窗
  const closeQRModal = () => {
    showQRModal.value = false;
    qrCodeBase64.value = '';
    qrLeaveItem.value = null;
    qrError.value = '';
  };

  // ===== 教师扫码核验 =====
  const handleScanVerify = () => {
    wx.scanCode({
      onlyFromCamera: false,
      scanType: ['qrCode'],
      success: (scanRes) => {
        const qrContent = scanRes.result;
        if (!qrContent) {
          wx.showToast({ title: '未识别到二维码', icon: 'none' });
          return;
        }

        const token = wx.getStorageSync('token');
        wx.showLoading({ title: '核验中...' });

        wx.request({
          url: `${BASE_URL}/leaves/verify-qr`,
          method: 'POST',
          data: { qr_content: qrContent },
          header: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          success: (res) => {
            const data = res.data as any;
            if (data && data.valid) {
              wx.showModal({
                title: '核验通过',
                content: `学生：${data.student_name || '-'}\n日期：${(data.leave_date || '').substring(0, 10)}\n类型：${data.leave_type || '-'}\n状态：${data.status || '-'}`,
                showCancel: false,
                confirmText: '确定',
              });
            } else {
              wx.showModal({
                title: '核验失败',
                content: data?.error_msg || '二维码无效',
                showCancel: false,
                confirmText: '确定',
              });
            }
          },
          fail: () => {
            wx.showToast({ title: '核验请求失败', icon: 'error' });
          },
          complete: () => {
            wx.hideLoading();
          },
        });
      },
      fail: () => {
        wx.showToast({ title: '扫码失败', icon: 'none' });
      },
    });
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
    leaveTypeOptions,
    selectedLeaveTypeIndex,
    userInfo,
    fetchLeaves,
    loadMore,
    onPullDownRefresh,
    goBack,
    noop: () => {},
    onReady,
    openCreateModal,
    closeCreateModal,
    onStudentIdInput,
    onDateChange,
    onLeaveHoursInput,
    onLeaveTypeInput,
    onRemarksInput,
    onCourseChange,
    onLeaveTypeChange,
    onGuaranteeStudentIdInput,
    handleCreateLeave,
    auditLeave,
    approveLeave,
    rejectLeave,
    showQRModal,
    qrLeaveItem,
    qrCodeBase64,
    qrLoading,
    qrError,
    qrValidInfo,
    showLeaveQR,
    closeQRModal,
    handleScanVerify,
    guaranteeLeave,
    isGuarantorFor,
    closeOffLeave,
    canCloseOff,
  };
});