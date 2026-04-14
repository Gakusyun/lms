import axios from 'axios'

// 创建axios实例
const http = axios.create({
  // 根据环境变量设置baseURL
  // 开发环境使用localhost，生产环境使用环境变量或默认生产地址
  baseURL: import.meta.env.DEV ? 'http://localhost:8000/api/v1' : (import.meta.env.VITE_API_BASE_URL || 'https://lms.gxj62.cn/api/v1'),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('HTTP请求错误:', error)

    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回错误状态码
      const status = error.response.status
      const message = error.response.data?.detail || '请求失败，请稍后再试'

      // 处理401未授权错误
      if (status === 401) {
        // 清除本地存储的token
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        // 跳转到登录页
        window.location.href = '/login'
      }

      // 处理404错误
      else if (status === 404) {
        console.error('请求的资源不存在')
      }

      // 处理500错误
      else if (status >= 500) {
        console.error('服务器内部错误')
      }

      // 显示错误消息
      if (message) {
        // 这里可以集成消息提示组件，如Element Plus的ElMessage
        console.error('错误消息:', message)
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('网络错误，请检查网络连接')
    } else {
      // 请求配置出错
      console.error('请求配置错误:', error.message)
    }

    return Promise.reject(error)
  }
)

export default http