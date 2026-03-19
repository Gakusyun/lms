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
    const response = await http.get('/logout')
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
    const response = await http.post(`/leaves/edit/${leaveId}`, leaveData)
    console.log('编辑请假条成功:', response)
    return response
  } catch (error: any) {
    console.error('编辑请假条失败:', error)
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

// 审核请假条API (实际上是编辑的一种特殊情况)
export const auditLeave = async (leaveId: number, auditData: {
  status: string
  audit_remarks?: string
}) => {
  try {
    console.log(`审核请假条 ${leaveId} 数据:`, auditData)
    const response = await http.post(`/leaves/edit/${leaveId}`, auditData)
    console.log('审核请假条成功:', response)
    return response
  } catch (error: any) {
    console.error('审核请假条失败:', error)
    if (error.response?.data) {
      console.error('错误详情:', error.response.data)
    }
    throw error
  }
}
