<template>
  <div class="db-config-page">
    <div class="db-config-container">
      <div class="db-config-card">
        <!-- Header -->
        <div class="config-header">
          <div class="config-logo">
            <div class="logo-icon">🗃️</div>
          </div>
          <h1 class="config-title">数据库配置</h1>
          <p class="config-subtitle">请配置数据库连接信息</p>
        </div>

        <div class="config-form-container">
          <form @submit.prevent="handleConfigureDatabase" class="config-form">
            <div class="form-group">
              <label for="dbType" class="form-label">数据库类型</label>
              <select id="dbType" v-model="dbForm.dbType" class="form-input" required>
                <option value="mysql">MySQL</option>
                <option value="sqlite">SQLite</option>
              </select>
            </div>

            <div v-if="dbForm.dbType === 'mysql'" class="mysql-settings">
              <div class="form-group">
                <label for="host" class="form-label">主机地址</label>
                <input type="text" id="host" v-model="dbForm.host" class="form-input" required placeholder="localhost" />
              </div>

              <div class="form-group">
                <label for="port" class="form-label">端口</label>
                <input type="number" id="port" v-model="dbForm.port" class="form-input" required placeholder="3306" />
              </div>

              <div class="form-group">
                <label for="database" class="form-label">数据库名</label>
                <input type="text" id="database" v-model="dbForm.database" class="form-input" required placeholder="leave_management" />
              </div>

              <div class="form-group">
                <label for="username" class="form-label">用户名</label>
                <input type="text" id="username" v-model="dbForm.username" class="form-input" required placeholder="root" />
              </div>

              <div class="form-group">
                <label for="password" class="form-label">密码</label>
                <input type="password" id="password" v-model="dbForm.password" class="form-input" placeholder="留空表示无密码" />
              </div>
            </div>

            <div v-else class="sqlite-settings">
              <div class="form-group">
                <label for="dbPath" class="form-label">数据库文件路径</label>
                <input type="text" id="dbPath" v-model="dbForm.dbPath" class="form-input" required placeholder="./leave_management.db" />
              </div>
            </div>

            <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="isLoading">
              <span v-if="!isLoading">配置数据库</span>
              <span v-else>配置中...</span>
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

const dbForm = reactive({
  dbType: 'mysql',
  host: 'localhost',
  port: 3306,
  database: 'leave_management',
  username: 'root',
  password: '',
  dbPath: './leave_management.db'
})

const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const handleConfigureDatabase = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    const configData = {
      db_type: dbForm.dbType,
      host: dbForm.host,
      port: dbForm.port,
      database: dbForm.database,
      username: dbForm.username,
      password: dbForm.password,
      db_path: dbForm.dbPath
    }

    console.log('数据库配置数据:', configData)

    // Call API to configure database
    const response = await http.post('/admin/configure-db', configData)

    console.log('数据库配置成功:', response)
    successMessage.value = '数据库配置成功！系统正在初始化...'

    // Delay redirect to login page
    setTimeout(() => {
      router.push('/login')
    }, 2000)

  } catch (error: any) {
    console.error('数据库配置失败:', error)
    errorMessage.value = error.response?.data?.message || '数据库配置失败，请重试'
  } finally {
    isLoading.value = false
  }
}

// Check if admin is already created
onMounted(async () => {
  try {
    // Check system health
    const healthResponse = await http.get('/')
    
    // If system is healthy, redirect to login
    if (healthResponse.data.status === 'healthy') {
      router.replace('/login')
      return
    }

  } catch (error) {
    console.error('健康检查失败:', error)
    // Continue to database configuration
  }
})
</script>

<style scoped>
.db-config-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--bg-secondary) 100%);
  padding: var(--spacing);
}

.db-config-container {
  width: 100%;
  max-width: 500px;
}

.db-config-card {
  background-color: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-xl);
  border: 1px solid var(--border-light);
}

.config-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.config-logo {
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

.config-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  line-height: var(--leading-tight);
}

.config-subtitle {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
  font-weight: 500;
}

.config-form-container {
  margin-bottom: var(--spacing);
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
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

/* Responsive design */
@media (max-width: 768px) {
  .db-config-page {
    padding: var(--spacing-sm);
  }

  .db-config-container {
    max-width: 100%;
  }

  .db-config-card {
    padding: var(--spacing-lg);
  }

  .config-logo {
    width: 56px;
    height: 56px;
  }

  .logo-icon {
    font-size: 1.75rem;
  }

  .config-title {
    font-size: var(--text-xl);
  }

  .config-subtitle {
    font-size: var(--text-sm);
  }
}

@media (max-width: 480px) {
  .db-config-card {
    padding: var(--spacing);
  }

  .config-logo {
    width: 48px;
    height: 48px;
  }

  .logo-icon {
    font-size: 1.5rem;
  }

  .config-title {
    font-size: var(--text-lg);
  }

  .config-subtitle {
    font-size: var(--text-xs);
  }

  .form-input {
    padding: 0.625rem 0.875rem;
    font-size: var(--text-sm);
  }
}
</style>