import { defineComponent, ref } from '@vue-mini/core';
import { BASE_URL } from '@/app';
import { requireAuth } from '@/utils/auth';

interface StudentCourse {
  student_id: number;
  student_name: string;
  course_name: string;
  course_id: number;
  teacher_name: string;
  enrollment_date: string;
  status: string;
}

export default defineComponent(() => {
  const courseId = ref(0);
  const courseName = ref('');
  const students = ref<StudentCourse[]>([]);
  const loading = ref(false);
  const total = ref(0);

  // 获取 URL 参数（小程序通过 onLoad 获取）
  const onLoad = (options: any) => {
    if (options && options.courseId) {
      courseId.value = parseInt(options.courseId);
      courseName.value = options.courseName || `课程 ${courseId.value}`;
    }
  };

  // 获取课程学生名单
  const fetchCourseStudents = () => {
    if (!courseId.value) return;

    loading.value = true;
    wx.showLoading({ title: '加载中...' });

    const token = wx.getStorageSync('token');
    wx.request({
      url: `${BASE_URL}/student-courses/course/${courseId.value}`,
      method: 'GET',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        const data = res.data as any;
        if (Array.isArray(data)) {
          students.value = data;
          total.value = data.length;
        } else if (data && Array.isArray(data.items)) {
          students.value = data.items;
          total.value = data.items.length;
        }
        wx.stopPullDownRefresh();
      },
      fail: () => {
        wx.showToast({ title: '加载失败', icon: 'error' });
        wx.stopPullDownRefresh();
      },
      complete: () => {
        loading.value = false;
        wx.hideLoading();
      }
    });
  };

  // 下拉刷新
  const onPullDownRefresh = () => {
    fetchCourseStudents();
  };

  // 返回上一页
  const goBack = () => {
    wx.navigateBack();
  };

  // 页面加载时获取数据
  const onReady = async () => {
    const user = await requireAuth();
    if (user) {
      if (courseId.value) {
        fetchCourseStudents();
      }
    }
  };

  return {
    courseId,
    courseName,
    students,
    loading,
    total,
    onLoad,
    onPullDownRefresh,
    goBack,
    onReady
  };
});
