<template>
  <div class="initial-setup-page">
    <div class="initial-setup-container">
      <div class="initial-setup-card">
        <!-- Header -->
        <div class="setup-header">
          <div class="setup-logo">
            <div class="logo-icon">🚀</div>
          </div>
          <h1 class="setup-title">系统初始化</h1>
          <p class="setup-subtitle">首次使用系统，需要配置数据库并创建管理员账户</p>
        </div>

        <div class="setup-form-container">
          <form @submit.prevent="handleSetup" class="setup-form">
            <!-- 数据库配置 -->
            <div class="form-section">
              <h2 class="section-title">数据库配置</h2>
              
              <div class="form-group">
                <label for="dbType" class="form-label">数据库类型</label>
                <select id="dbType" v-model="setupForm.dbType" class="form-input" required>
                  <option value="mysql">MySQL</option>
                  <option value="sqlite">SQLite</option>
                </select>
              </div>

              <div v-if="setupForm.dbType === 'mysql'" class="mysql-settings">
                <div class="form-group">
                  <label for="host" class="form-label">主机地址</label>
                  <input type="text" id="host" v-model="setupForm.host" class="form-input" required placeholder="localhost" />
                </div>

                <div class="form-group">
                  <label for="port" class="form-label">端口</label>
                  <input type="number" id="port" v-model="setupForm.port" class="form-input" required placeholder="3306" />
                </div>

                <div class="form-group">
                  <label for="database" class="form-label">数据库名</label>
                  <input type="text" id="database" v-model="setupForm.database" class="form-input" required placeholder="leave_management" />
                </div>

                <div class="form-group">
                  <label for="username" class="form-label">用户名</label>
                  <input type="text" id="username" v-model="setupForm.username" class="form-input" required placeholder="root" />
                </div>

                <div class="form-group">
                  <label for="password" class="form-label">密码</label>
                  <input type="password" id="password" v-model="setupForm.password" class="form-input" placeholder="留空表示无密码" />
                </div>
              </div>

              <div v-else class="sqlite-settings">
                <div class="form-group">
                  <label for="dbPath" class="form-label">数据库文件路径</label>
                  <input type="text" id="dbPath" v-model="setupForm.dbPath" class="form-input" required placeholder="./leave_management.db" />
                </div>
              </div>

              <button type="button" @click="handleTestConnection" class="btn btn-secondary w-full mt-2" :disabled="isTesting">
                <span v-if="!isTesting">🔍 测试连接</span>
                <span v-else>测试中...</span>
              </button>

              <div v-if="connectionStatus" :class="['connection-status', connectionStatus.success ? 'success' : 'error']" class="mt-2">
                <span v-if="connectionStatus.success">✅ 连接成功！</span>
                <span v-else>❌ 连接失败：{{ connectionStatus.message }}</span>
              </div>
            </div>

            <!-- 管理员信息 -->
            <div class="form-section">
              <h2 class="section-title">管理员信息</h2>
              
              <div class="form-group">
                <label for="admin_id" class="form-label">管理员ID</label>
                <input type="number" id="admin_id" v-model="setupForm.admin_id" class="form-input" required placeholder="请输入管理员ID（数字）" min="1" />
              </div>

              <div class="form-group">
                <label for="name" class="form-label">管理员姓名</label>
                <input type="text" id="name" v-model="setupForm.name" class="form-input" required placeholder="请输入管理员姓名（最多8个字符）" maxlength="8" />
              </div>

              <div class="form-group">
                <label for="adminPassword" class="form-label">密码</label>
                <input type="password" id="adminPassword" v-model="setupForm.adminPassword" class="form-input" required placeholder="请输入密码" />
              </div>
            </div>

            <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="isLoading || !connectionStatus?.success">
              <span v-if="!isLoading">完成初始化</span>
              <span v-else>初始化中...</span>
            </button>
          </form>

          <!-- Error message -->
          <div v-if="errorMessage" class="alert alert-danger mt-4">
            {{ errorMessage }}
          </div>

          <!-- Success message -->
          <div v-if="successMessage" class="alert alert-success mt-4">
            {{ successMessage }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../utils/http'

const router = useRouter()

const setupForm = reactive({
  // 数据库配置
  dbType: 'mysql',
  host: 'localhost',
  port: 3306,
  database: 'leave_management',
  username: 'root',
  password: '',
  dbPath: './leave_management.db',
  // 管理员信息
  admin_id: '',
  name: '',
  adminPassword: ''
})

const isLoading = ref(false)
const isTesting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const connectionStatus = ref<{ success: boolean; message: string } | null>(null)

const handleTestConnection = async () => {
  try {
    isTesting.value = true
    errorMessage.value = ''
    connectionStatus.value = null

    const configData = {
      db_type: setupForm.dbType,
      host: setupForm.host,
      port: setupForm.port,
      database: setupForm.database,
      username: setupForm.username,
      password: setupForm.password,
      db_path: setupForm.dbPath
    }

    console.log('测试数据库连接:', configData)

    // 调用数据库连接测试API
    const response = await http.post('/admin/test-db-connection', configData)

    console.log('数据库连接测试成功:', response)
    connectionStatus.value = { success: true, message: '连接成功' }

  } catch (error: any) {
    console.error('数据库连接测试失败:', error)
    connectionStatus.value = { 
      success: false, 
      message: error.response?.data?.message || '连接失败，请检查配置' 
    }
  } finally {
    isTesting.value = false
  }
}

const handleSetup = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    // 1. 配置数据库
    const dbConfigData = {
      db_type: setupForm.dbType,
      host: setupForm.host,
      port: setupForm.port,
      database: setupForm.database,
      username: setupForm.username,
      password: setupForm.password,
      db_path: setupForm.dbPath
    }

    console.log('配置数据库:', dbConfigData)
    const dbResponse = await http.post('/admin/configure-db', dbConfigData)
    console.log('数据库配置成功:', dbResponse)

    // 2. 创建管理员
    const adminData = {
      admin_id: parseInt(setupForm.admin_id),
      name: setupForm.name,
      password: setupForm.adminPassword
    }

    console.log('创建管理员:', adminData)
    const adminResponse = await http.post('/create/admin', adminData)
    console.log('管理员创建成功:', adminResponse)

    successMessage.value = '系统初始化成功！正在跳转到登录页面...'

    // 延迟跳转到登录页面
    setTimeout(() => {
      router.push('/login')
    }, 2000)

  } catch (error: any) {
    console.error('系统初始化失败:', error)
    errorMessage.value = error.response?.data?.message || '初始化失败，请重试'
  } finally {
    isLoading.value = false
  }
}

// 检查系统健康状态
onMounted(async () => {
  try {
    console.log('检查系统健康状态...')
    const healthResponse = await http.get('/')
    
    // If system is healthy, redirect to login
    if (healthResponse.status === 'healthy') {
      console.log('系统已初始化，跳转到登录页面')
      router.replace('/login')
      return
    }

  } catch (error) {
    console.error('健康检查失败:', error)
    // Continue to setup
  }
})
</script>

<style scoped>
.initial-setup-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--bg-secondary) 100%);
  padding: var(--spacing);
}

.initial-setup-container {
  width: 100%;
  max-width: 600px;
}

.initial-setup-card {
  background-color: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-xl);
  border: 1px solid var(--border-light);
}

.setup-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.setup-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: var(--radius-xl);
  margin: 0 auto var(--spacing);
  box-shadow: var(--shadow-lg);
}

.logo-icon {
  font-size: 2rem;
  color: var(--text-inverse);
}

.setup-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  line-height: var(--leading-tight);
}

.setup-subtitle {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
  font-weight: 500;
}

.setup-form-container {
  margin-bottom: var(--spacing);
}

.setup-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-section {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-light);
}

.section-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing) 0;
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-light);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.form-input {
  padding: 0.75rem 1rem;
  font-size: var(--text-base);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: all var(--transition);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

.mysql-settings,
.sqlite-settings {
  margin-top: var(--spacing);
  padding-top: var(--spacing);
  border-top: 1px solid var(--border-light);
}

.connection-status {
  padding: 0.75rem;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: 500;
  text-align: center;
}

.connection-status.success {
  background-color: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.connection-status.error {
  background-color: rgba(220, 53, 69, 0.1);
  color: #dc3545;
  border: 1px solid rgba(220, 53, 69, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .initial-setup-page {
    padding: var(--spacing-sm);
  }

  .initial-setup-container {
    max-width: 100%;
  }

  .initial-setup-card {
    padding: var(--spacing-lg);
  }

  .setup-logo {
    width: 56px;
    height: 56px;
  }

  .logo-icon {
    font-size: 1.75rem;
  }

  .setup-title {
    font-size: var(--text-xl);
  }

  .setup-subtitle {
    font-size: var(--text-sm);
  }

  .form-section {
    padding: var(--spacing);
  }

  .section-title {
    font-size: var(--text-base);
  }
}

@media (max-width: 480px) {
  .initial-setup-card {
    padding: var(--spacing);
  }

  .setup-logo {
    width: 48px;
    height: 48px;
  }

  .logo-icon {
    font-size: 1.5rem;
  }

  .setup-title {
    font-size: var(--text-lg);
  }

  .setup-subtitle {
    font-size: var(--text-xs);
  }

  .form-input {
    padding: 0.625rem 0.875rem;
    font-size: var(--text-sm);
  }
}
</style>