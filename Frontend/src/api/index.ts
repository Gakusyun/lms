import http from '../utils/http'

// GET请求示例
export const getData = async (url: string, params?: any) => {
  try {
    console.log(`GET请求 ${url}，参数:`, params)
    const response = await http.get(url, { params })
    console.log(`GET请求成功 ${url}，响应:`, response)
    return response
  } catch (error) {
    console.error('GET请求失败:', error)
    throw error
  }
}

// 分页数据请求 - 仅使用GET方法
export const getPagedData = async (url: string, page: number = 1, pageSize: number = 20, params?: any) => {
  try {
    const requestData = {
      page,
      page_size: pageSize,
      ...params
    }

    // 直接使用GET方法
    const response = await http.get(url, { params: requestData })
    return response
  } catch (error) {
    console.error('分页请求失败:', error)
    throw error
  }
}

// POST请求示例
export const postData = async (url: string, data?: any) => {
  try {
    const response = await http.post(url, data)
    return response
  } catch (error) {
    console.error('POST请求失败:', error)
    throw error
  }
}

// 登录API
export const login = async (loginData: {
  id: string
  password: string
}) => {
  try {
    // 转换id为数字类型，因为后端期望的是整数
    const data = {
      id: parseInt(loginData.id),
      password: loginData.password
    }
    const response = await http.post('/login', data)
    return response
  } catch (error) {
    console.error('登录失败:', error)
    throw error
  }
}

// 检查登录状态API
export const checkAuth = async () => {
  try {
    const response = await http.get('/login/check')
    return response
  } catch (error) {
    console.error('检查登录状态失败:', error)
    throw error
  }
}

// 退出登录API
export const logout = async () => {
  try {
    const response = await http.post('/logout')
    return response
  } catch (error) {
    console.error('退出登录失败:', error)
    throw error
  }
}

// 修改密码API（修改自己的密码）
export const changePassword = async (data: {
  old_password: string
  new_password: string
}) => {
  try {
    const response = await http.post('/change-password', data)
    return response
  } catch (error) {
    console.error('修改密码失败:', error)
    throw error
  }
}

// 修改指定用户密码API（仅管理员可用）
export const changeUserPassword = async (userId: number, data: {
  old_password: string
  new_password: string
}) => {
  try {
    const response = await http.post(`/change-password/${userId}`, data)
    return response
  } catch (error) {
    console.error('修改用户密码失败:', error)
    throw error
  }
}

// 系统健康检查API
export const checkSystemHealth = async () => {
  try {
    const response = await http.get('/')
    return response
  } catch (error) {
    console.error('系统健康检查失败:', error)
    throw error
  }
}

// 创建管理员API
export const createAdmin = async (adminData: {
  admin_id: number
  name: string
  password: string
}) => {
  try {
    const response = await http.post('/create/admin', adminData)
    return response
  } catch (error) {
    console.error('创建管理员失败:', error)
    throw error
  }
}

// 获取所有课程API
export const getAllCourses = async () => {
  try {
    console.log('获取所有课程')
    const response = await http.get('/courses')
    console.log('获取所有课程成功:', response)
    return response
  } catch (error) {
    console.error('获取所有课程失败:', error)
    throw error
  }
}

// 创建请假条API
export const createLeave = async (leaveData: any) => {
  try {
    console.log('创建请假条数据:', leaveData)
    const response = await http.post('/leaves', leaveData)
    console.log('创建请假条成功:', response)
    return response
  } catch (error: any) {
    console.error('创建请假条失败:', error)
    if (error.response?.data) {
      console.error('错误详情:', error.response.data)
      if (error.response.data.detail) {
        console.error('验证错误详情:', error.response.data.detail)
        // 如果是数组，逐个输出
        if (Array.isArray(error.response.data.detail)) {
          error.response.data.detail.forEach((item: any, index: number) => {
            console.error(`验证错误 ${index + 1}:`, item)
          })
        }
      }
    }
    throw error
  }
}

// 学生选课API
export const createStudentCourse = async (studentCourseData: {
  student_id: number
  course_id: number
  enrollment_date?: string
  status?: string
}) => {
  try {
    console.log('学生选课数据:', studentCourseData)
    const response = await http.post('/student-courses', studentCourseData)
    console.log('学生选课成功:', response)
    return response
  } catch (error) {
    console.error('学生选课失败:', error)
    throw error
  }
}

// 获取学生的选课列表API
export const getStudentCourses = async (studentId: number) => {
  try {
    console.log(`获取学生 ${studentId} 的选课列表`)
    const response = await http.get(`/student-courses/student/${studentId}`)
    console.log('获取学生选课列表成功:', response)
    return response
  } catch (error) {
    console.error('获取学生选课列表失败:', error)
    throw error
  }
}

// 获取课程的学生列表API
export const getCourseStudents = async (courseId: number) => {
  try {
    console.log(`获取课程 ${courseId} 的学生列表`)
    const response = await http.get(`/student-courses/course/${courseId}`)
    console.log('获取课程学生列表成功:', response)
    return response
  } catch (error) {
    console.error('获取课程学生列表失败:', error)
    throw error
  }
}

// 获取课程的选课人数API
export const getCourseEnrollmentCount = async (courseId: number) => {
  try {
    console.log(`获取课程 ${courseId} 的选课人数`)
    const response = await http.get(`/student-courses/course/${courseId}/count`)
    console.log('获取课程选课人数成功:', response)
    return response
  } catch (error) {
    console.error('获取课程选课人数失败:', error)
    throw error
  }
}

// 编辑请假条API
export const editLeave = async (leaveId: number, leaveData: any) => {
  try {
    console.log(`编辑请假条 ${leaveId} 数据:`, leaveData)
    const response = await http.put(`/leaves/edit/${leaveId}`, leaveData)
    console.log('编辑请假条成功:', response)
    return response
  } catch (error: any) {
    console.error('编辑请假条失败:', error)
    if (error.response?.data) {
      console.error('错误详情:', error.response.data)
      if (error.response.data.detail) {
        console.error('验证错误详情:', error.response.data.detail)
        if (Array.isArray(error.response.data.detail)) {
          error.response.data.detail.forEach((item: any, index: number) => {
            console.error(`验证错误 ${index + 1}:`, item)
          })
        }
      }
    }
    throw error
  }
}

// 批准请假条API
export const approveLeave = async (leaveId: number, auditRemarks: string = '') => {
  try {
    const response = await http.post(`/leaves/approve/${leaveId}`, null, {
      params: { audit_remarks: auditRemarks }
    })
    return response
  } catch (error) {
    console.error('批准请假条失败:', error)
    throw error
  }
}

// 拒绝请假条API
export const rejectLeave = async (leaveId: number, auditRemarks: string = '') => {
  try {
    const response = await http.post(`/leaves/reject/${leaveId}`, null, {
      params: { audit_remarks: auditRemarks }
    })
    return response
  } catch (error) {
    console.error('拒绝请假条失败:', error)
    throw error
  }
}

// 撤销请假条API
export const cancelLeave = async (leaveId: number) => {
  try {
    const response = await http.post(`/leaves/cancel/${leaveId}`)
    return response
  } catch (error) {
    console.error('撤销请假条失败:', error)
    throw error
  }
}

// 获取请假凭证二维码API
export const getLeaveQRCode = async (leaveId: number) => {
  try {
    const response = await http.get(`/leaves/${leaveId}/qr`)
    return response
  } catch (error) {
    console.error('获取二维码失败:', error)
    throw error
  }
}

// 核验二维码API
export const verifyQRCode = async (qrContent: string) => {
  try {
    const response = await http.post('/leaves/verify-qr', { qr_content: qrContent })
    return response
  } catch (error) {
    console.error('核验二维码失败:', error)
    throw error
  }
}

// 获取智能审批推荐API
export const getApprovalRecommendation = async (leaveId: number) => {
  try {
    const response = await http.get(`/leaves/${leaveId}/recommendation`)
    return response
  } catch (error) {
    console.error('获取审批推荐失败:', error)
    throw error
  }
}

// 统计API
export const getLeaveStatistics = async () => {
  try {
    const response = await http.get('/statistics/leaves')
    return response
  } catch (error) {
    console.error('获取请假统计失败:', error)
    throw error
  }
}

export const getLeaveTrend = async (days: number = 30) => {
  try {
    const response = await http.get('/statistics/leaves/trend', { params: { days } })
    return response
  } catch (error) {
    console.error('获取请假趋势失败:', error)
    throw error
  }
}

export const getUserStatistics = async () => {
  try {
    const response = await http.get('/statistics/users')
    return response
  } catch (error) {
    console.error('获取用户统计失败:', error)
    throw error
  }
}

export const getReviewerStudentsStatistics = async () => {
  try {
    const response = await http.get('/statistics/reviewers/students')
    return response
  } catch (error) {
    console.error('获取审核员学生统计失败:', error)
    throw error
  }
}

// 通知API
export const getNotifications = async (params?: any) => {
  try {
    const response = await http.get('/notifications', { params })
    return response
  } catch (error) {
    console.error('获取通知失败:', error)
    throw error
  }
}

export const getUnreadCount = async () => {
  try {
    const response = await http.get('/notifications/unread-count')
    return response
  } catch (error) {
    console.error('获取未读数量失败:', error)
    throw error
  }
}

export const markNotificationRead = async (notificationId: number) => {
  try {
    const response = await http.post(`/notifications/${notificationId}/read`)
    return response
  } catch (error) {
    console.error('标记已读失败:', error)
    throw error
  }
}

export const markAllNotificationsRead = async () => {
  try {
    const response = await http.post('/notifications/read-all')
    return response
  } catch (error) {
    console.error('全部标记已读失败:', error)
    throw error
  }
}

// JSON导出API
export const exportLeavesJSON = async () => {
  try {
    const response = await http.get('/export/leaves/json', { responseType: 'blob' })
    return response
  } catch (error) {
    console.error('导出请假数据失败:', error)
    throw error
  }
}

export const exportStudentsJSON = async () => {
  try {
    const response = await http.get('/export/students/json', { responseType: 'blob' })
    return response
  } catch (error) {
    console.error('导出学生数据失败:', error)
    throw error
  }
}

// 销假API - 辅导员确认学生已返校报到
export const closeOffLeave = async (leaveId: number, penaltyDays?: number) => {
  try {
    const response = await http.post(`/leaves/close-off/${leaveId}`, null, {
      params: penaltyDays ? { penalty_days: penaltyDays } : undefined
    })
    return response
  } catch (error) {
    console.error('销假失败:', error)
    throw error
  }
}

// 担保请假条API - 紧急请假担保生效
export const guaranteeLeave = async (leaveId: number) => {
  try {
    const response = await http.post(`/leaves/guarantee/${leaveId}`)
    return response
  } catch (error) {
    console.error('担保失败:', error)
    throw error
  }
}

// 学生退课API
export const deleteStudentCourse = async (studentId: number, courseId: number) => {
  try {
    const response = await http.delete(`/student-courses/student/${studentId}/course/${courseId}`)
    return response
  } catch (error) {
    console.error('退课失败:', error)
    throw error
  }
}

// 上传证明文件API
export const uploadLeaveFile = async (file: File) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    // 注意：不设置 Content-Type，让 Axios 自动添加带 boundary 的 multipart/form-data
    const response = await http.post('/leaves/upload', formData)
    return response
  } catch (error) {
    console.error('上传文件失败:', error)
    throw error
  }
}

// 上传请假证明文件到指定请假条API
export const uploadLeaveFiles = async (leaveId: number, files: File[]) => {
  try {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    const response = await http.post(`/leaves/${leaveId}/upload`, formData)
    return response
  } catch (error) {
    console.error('上传文件失败:', error)
    throw error
  }
}

// 下载学生导入模板
export const downloadStudentImportTemplate = async () => {
  try {
    const response = await http.get('/students/import/template', { responseType: 'blob' })
    return response
  } catch (error) {
    console.error('下载模板失败:', error)
    throw error
  }
}

// 批量导入学生
export const importStudents = async (file: File) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await http.post('/students/import', formData)
    return response
  } catch (error) {
    console.error('导入学生失败:', error)
    throw error
  }
}
