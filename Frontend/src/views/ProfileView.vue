<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { changePassword } from '../api/index'
import http from '../utils/http'
import { Html5Qrcode } from 'html5-qrcode'

const router = useRouter()

// 用户信息
const userInfo = ref({
  id: '',
  name: '',
  role: ''
})

// 修改密码表单
const showPasswordModal = ref(false)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const passwordLoading = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')

// 角色中文映射
const roleMap: { [key: string]: string } = {
  admin: '管理员',
  reviewer: '审核员',
  teacher: '教师',
  student: '学生'
}

// 获取用户信息
const getUserInfo = () => {
  const id = localStorage.getItem('id')
  const name = localStorage.getItem('name')
  const role = localStorage.getItem('role')

  if (id && name && role) {
    userInfo.value = { id, name, role }
  }
}

// 返回首页
const goHome = () => {
  router.push('/')
}

// 退出登录
const logout = () => {
  localStorage.clear()
  router.push('/login')
}

// 修改姓名
const isEditingName = ref(false)
const editNameValue = ref('')
const nameError = ref('')
const nameSuccess = ref('')

const startEditName = () => {
  editNameValue.value = userInfo.value.name
  isEditingName.value = true
  nameError.value = ''
  nameSuccess.value = ''
}

const cancelEditName = () => {
  isEditingName.value = false
  editNameValue.value = ''
  nameError.value = ''
}

const handleSaveName = async () => {
  if (!editNameValue.value.trim()) {
    nameError.value = '姓名不能为空'
    return
  }

  try {
    nameError.value = ''
    nameSuccess.value = ''
    const response = await http.put('/profile', { name: editNameValue.value.trim() }) as any
    if (response?.name) {
      userInfo.value.name = response.name
      localStorage.setItem('name', response.name)
      nameSuccess.value = '姓名修改成功！'
      setTimeout(() => {
        isEditingName.value = false
        nameSuccess.value = ''
      }, 1500)
    }
  } catch (error: any) {
    nameError.value = error.response?.data?.detail || '修改失败'
  }
}

// 打开修改密码模态框
const openPasswordModal = () => {
  showPasswordModal.value = true
  passwordError.value = ''
  passwordSuccess.value = ''
  passwordForm.value = {
    old_password: '',
    new_password: '',
    confirm_password: ''
  }
}

// 关闭修改密码模态框
const closePasswordModal = () => {
  showPasswordModal.value = false
  passwordForm.value = {
    old_password: '',
    new_password: '',
    confirm_password: ''
  }
}

// 修改密码
const handleChangePassword = async () => {
  // 验证表单
  if (!passwordForm.value.old_password || !passwordForm.value.new_password || !passwordForm.value.confirm_password) {
    passwordError.value = '请填写所有字段'
    return
  }

  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    passwordError.value = '新密码和确认密码不一致'
    return
  }

  if (passwordForm.value.new_password.length < 6) {
    passwordError.value = '新密码长度不能少于6位'
    return
  }

  try {
    passwordLoading.value = true
    passwordError.value = ''
    passwordSuccess.value = ''

    const token = localStorage.getItem('token')
    if (!token) {
      throw new Error('未找到认证令牌')
    }

    await changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })

    passwordSuccess.value = '密码修改成功！'

    // 2秒后关闭模态框
    setTimeout(() => {
      closePasswordModal()
    }, 2000)

  } catch (error: any) {
    passwordError.value = error.response?.data?.detail || error.message || '修改密码失败'
  } finally {
    passwordLoading.value = false
  }
}

// ========== 让其他设备登录 ==========
const showOtherDeviceModal = ref(false)
const otherDeviceToken = ref('')
const otherDeviceLoading = ref(false)
const otherDeviceError = ref('')
const otherDeviceSuccess = ref('')

// 扫码相关
const showScanner = ref(false)
const scannerContainerId = 'qr-scanner-container'
let html5Qrcode: Html5Qrcode | null = null

const openOtherDeviceModal = () => {
  showOtherDeviceModal.value = true
  otherDeviceToken.value = ''
  otherDeviceError.value = ''
  otherDeviceSuccess.value = ''
}

const closeOtherDeviceModal = () => {
  showOtherDeviceModal.value = false
  stopScanner()
}

const handleManualToken = async () => {
  if (!otherDeviceToken.value.trim()) {
    otherDeviceError.value = '请输入登录令牌'
    return
  }
  await authorizeOtherDevice(otherDeviceToken.value.trim())
}

const startScanner = async () => {
  try {
    showScanner.value = true
    otherDeviceError.value = ''

    // 等待 DOM 就绪
    await new Promise(resolve => setTimeout(resolve, 100))

    html5Qrcode = new Html5Qrcode(scannerContainerId)

    await html5Qrcode.start(
      { facingMode: 'environment' },
      {
        fps: 10,
        qrbox: { width: 250, height: 250 }
      },
      (decodedText) => {
        // 扫码成功
        console.log('扫描到令牌:', decodedText)
        stopScanner()
        showScanner.value = false
        otherDeviceToken.value = decodedText
        authorizeOtherDevice(decodedText)
      },
      (_errorMessage) => {
        // 扫码错误（忽略，扫码中会持续输出）
      }
    )
  } catch (err) {
    console.error('启动摄像头失败:', err)
    otherDeviceError.value = '摄像头启动失败，请检查权限'
    showScanner.value = false
  }
}

const stopScanner = async () => {
  if (html5Qrcode && html5Qrcode.isScanning) {
    try {
      await html5Qrcode.stop()
    } catch (e) {
      // 忽略停止错误
    }
    html5Qrcode = null
  }
}

const authorizeOtherDevice = async (loginToken: string) => {
  try {
    otherDeviceLoading.value = true
    otherDeviceError.value = ''
    otherDeviceSuccess.value = ''

    const token = localStorage.getItem('token')
    if (!token) {
      throw new Error('未找到认证令牌')
    }

    // 调用后端 API，将当前用户的 JWT 与 login_token 绑定
    // 小程序端扫码：GET /login/orcode?login_token=xxx&token=JWT
    const response = await http.get('/login/orcode', {
      params: {
        login_token: loginToken,
        token: token
      }
    }) as any

    if (response && response.token) {
      otherDeviceSuccess.value = '授权成功！对方设备已登录'
      setTimeout(() => {
        closeOtherDeviceModal()
      }, 1500)
    } else {
      otherDeviceError.value = '授权失败，未获取到有效响应'
    }
  } catch (error: any) {
    console.error('授权失败:', error)
    otherDeviceError.value = error.response?.data?.detail || '授权失败，令牌无效或已过期'
  } finally {
    otherDeviceLoading.value = false
  }
}

onMounted(() => {
  getUserInfo()
})

onUnmounted(() => {
  stopScanner()
})
</script>

<template>
  <div class="profile-page">
    <div class="container">
      <!-- 页面头部 -->
      <div class="page-header">
        <h1 class="page-title">个人资料</h1>
        <div class="header-buttons">
          <button @click="goHome" class="btn btn-back">返回首页</button>
          <button @click="logout" class="btn btn-logout">退出登录</button>
        </div>
      </div>

      <!-- 用户信息卡片 -->
      <div class="profile-card">
        <div class="profile-header">
          <div class="avatar">
            <span class="avatar-text">{{ userInfo.name?.charAt(0) || 'U' }}</span>
          </div>
          <h2 class="user-name">{{ userInfo.name }}</h2>
          <span class="user-role">{{ roleMap[userInfo.role] || userInfo.role }}</span>
        </div>

        <div class="profile-info">
          <div class="info-item">
            <label>用户ID</label>
            <span>{{ userInfo.id }}</span>
          </div>
          <div class="info-item">
            <label>角色</label>
            <span>{{ roleMap[userInfo.role] || userInfo.role }}</span>
          </div>
          <div class="info-item">
            <label>姓名</label>
            <div v-if="!isEditingName" class="info-value-group">
              <span>{{ userInfo.name }}</span>
              <button @click="startEditName" class="btn-edit">修改</button>
            </div>
            <div v-else class="info-edit-group">
              <input
                type="text"
                v-model="editNameValue"
                class="form-input form-input-sm"
                placeholder="请输入新姓名"
                maxlength="20"
              />
              <button @click="handleSaveName" class="btn-save">保存</button>
              <button @click="cancelEditName" class="btn-cancel">取消</button>
            </div>
          </div>
          <div v-if="nameError" class="alert alert-danger" style="margin-top: -0.5rem;">
            {{ nameError }}
          </div>
          <div v-if="nameSuccess" class="alert alert-success" style="margin-top: -0.5rem;">
            {{ nameSuccess }}
          </div>
        </div>

        <div class="profile-actions">
          <button @click="openPasswordModal" class="btn btn-primary">
            修改密码
          </button>
          <button @click="openOtherDeviceModal" class="btn btn-secondary" style="margin-left: 0.5rem;">
            让其他设备登录
          </button>
        </div>
      </div>
    </div>

    <!-- 修改密码模态框 -->
    <div v-if="showPasswordModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h3>修改密码</h3>
          <button @click="closePasswordModal" class="modal-close">×</button>
        </div>

        <div class="modal-body">
          <!-- 错误信息 -->
          <div v-if="passwordError" class="alert alert-danger">
            {{ passwordError }}
          </div>

          <!-- 成功信息 -->
          <div v-if="passwordSuccess" class="alert alert-success">
            {{ passwordSuccess }}
          </div>

          <form @submit.prevent="handleChangePassword">
            <div class="form-group">
              <label for="old_password">当前密码</label>
              <input
                type="password"
                id="old_password"
                v-model="passwordForm.old_password"
                class="form-input"
                placeholder="请输入当前密码"
                required
              />
            </div>

            <div class="form-group">
              <label for="new_password">新密码</label>
              <input
                type="password"
                id="new_password"
                v-model="passwordForm.new_password"
                class="form-input"
                placeholder="请输入新密码（至少6位）"
                minlength="6"
                required
              />
            </div>

            <div class="form-group">
              <label for="confirm_password">确认新密码</label>
              <input
                type="password"
                id="confirm_password"
                v-model="passwordForm.confirm_password"
                class="form-input"
                placeholder="请再次输入新密码"
                minlength="6"
                required
              />
            </div>

            <div class="form-actions">
              <button type="button" @click="closePasswordModal" class="btn btn-outline">
                取消
              </button>
              <button type="submit" class="btn btn-primary" :disabled="passwordLoading">
                {{ passwordLoading ? '修改中...' : '确认修改' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 让其他设备登录模态框 -->
    <div v-if="showOtherDeviceModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h3>让其他设备登录</h3>
          <button @click="closeOtherDeviceModal" class="modal-close">×</button>
        </div>

        <div class="modal-body">
          <!-- 错误信息 -->
          <div v-if="otherDeviceError" class="alert alert-danger">
            {{ otherDeviceError }}
          </div>

          <!-- 成功信息 -->
          <div v-if="otherDeviceSuccess" class="alert alert-success">
            {{ otherDeviceSuccess }}
          </div>

          <!-- 扫码区域 -->
          <div v-if="showScanner" class="scanner-area">
            <div :id="scannerContainerId" class="scanner-container"></div>
            <button type="button" @click="stopScanner(); showScanner = false" class="btn btn-outline btn-sm">
              取消扫码
            </button>
          </div>

          <!-- 手动输入 -->
          <div v-else class="other-device-form">
            <p class="help-text">扫描其他设备显示的登录二维码，或手动输入登录令牌</p>

            <div class="form-group">
              <label for="other_device_token">登录令牌</label>
              <input
                type="text"
                id="other_device_token"
                v-model="otherDeviceToken"
                class="form-input"
                placeholder="请输入登录令牌"
              />
            </div>

            <div class="form-actions">
              <button type="button" @click="startScanner" class="btn btn-secondary" :disabled="otherDeviceLoading">
                扫码
              </button>
              <button type="button" @click="handleManualToken" class="btn btn-primary" :disabled="otherDeviceLoading">
                {{ otherDeviceLoading ? '授权中...' : '确认授权' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  padding: var(--spacing-xl);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing);
  border-bottom: 1px solid var(--border-light);
}

.page-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-buttons {
  display: flex;
  gap: var(--spacing);
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-weight: 500;
  transition: all var(--transition);
  cursor: pointer;
  border: none;
}

.btn-back {
  background-color: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
}

.btn-back:hover {
  background-color: var(--gray-200);
  color: var(--text-primary);
}

.btn-logout {
  background-color: var(--red-500);
  color: white;
}

.btn-logout:hover {
  background-color: var(--red-600);
}

.btn-primary {
  background-color: var(--primary-500);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-600);
}

.btn-primary:disabled {
  background-color: var(--gray-300);
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--primary-600);
  color: white;
}

.btn-secondary:hover {
  background-color: var(--primary-700);
}

.btn-secondary:disabled {
  background-color: var(--gray-300);
  cursor: not-allowed;
}

.btn-outline {
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
}

.btn-outline:hover {
  background-color: var(--gray-100);
  color: var(--text-primary);
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: var(--text-sm);
  margin-top: var(--spacing);
}

.profile-card {
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--spacing-2xl);
  max-width: 600px;
  margin: 0 auto;
}

.profile-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
}

.avatar {
  width: 100px;
  height: 100px;
  background-color: var(--primary-500);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing);
}

.avatar-text {
  font-size: 2.5rem;
  font-weight: 700;
  color: white;
}

.user-name {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm);
}

.user-role {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background-color: var(--primary-100);
  color: var(--primary-700);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  font-weight: 500;
}

.profile-info {
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
  padding: var(--spacing-xl) 0;
  margin-bottom: var(--spacing-xl);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing) 0;
}

.info-item label {
  font-weight: 500;
  color: var(--text-secondary);
}

.info-item span {
  font-weight: 600;
  color: var(--text-primary);
}

.info-value-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.info-edit-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.form-input-sm {
  padding: 0.35rem 0.5rem;
  font-size: var(--text-sm);
  width: 140px;
}

.btn-edit, .btn-save, .btn-cancel {
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--border-medium);
  background: var(--gray-50);
  color: var(--text-secondary);
  transition: all var(--transition);
}

.btn-edit:hover, .btn-save:hover, .btn-cancel:hover {
  background: var(--gray-100);
  color: var(--text-primary);
}

.btn-save {
  background-color: var(--primary-50);
  color: var(--primary-700);
  border-color: var(--primary-200);
}

.btn-save:hover {
  background-color: var(--primary-100);
}

.profile-actions {
  text-align: center;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-xl);
}

.form-group {
  margin-bottom: var(--spacing);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-base);
  transition: border-color var(--transition);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-500);
}

.form-actions {
  display: flex;
  gap: var(--spacing);
  justify-content: flex-end;
  margin-top: var(--spacing-xl);
}

.alert {
  padding: var(--spacing);
  border-radius: var(--radius);
  margin-bottom: var(--spacing);
}

.alert-danger {
  background-color: var(--red-50);
  color: var(--red-700);
  border: 1px solid var(--red-200);
}

.alert-success {
  background-color: var(--green-50);
  color: var(--green-700);
  border: 1px solid var(--green-200);
}

.help-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.scanner-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing);
}

.scanner-container {
  width: 250px;
  height: 250px;
  border: 2px solid var(--border-medium);
  border-radius: var(--radius);
  overflow: hidden;
}

.other-device-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}
</style>
