<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Html5Qrcode } from 'html5-qrcode'

const router = useRouter()
const qrContent = ref('')
const verifyResult = ref<any>(null)
const verifyError = ref('')
const isVerifying = ref(false)
const showScanner = ref(false)
const scannerContainerId = 'qr-scanner'
let html5Qrcode: Html5Qrcode | null = null

// 打开摄像头扫描
const startScanner = async () => {
  showScanner.value = true
  verifyError.value = ''

  await new Promise(resolve => setTimeout(resolve, 100))

  html5Qrcode = new Html5Qrcode(scannerContainerId)

  try {
    await html5Qrcode.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      (decodedText) => {
        console.log('扫描到内容:', decodedText)
        stopScanner()
        showScanner.value = false
        qrContent.value = decodedText
        handleVerify()
      },
      () => {}
    )
  } catch (err) {
    console.error('摄像头启动失败:', err)
    verifyError.value = '摄像头启动失败，请检查权限'
    showScanner.value = false
  }
}

const stopScanner = async () => {
  if (html5Qrcode && html5Qrcode.isScanning) {
    try {
      await html5Qrcode.stop()
    } catch (e) {}
    html5Qrcode = null
  }
}

const closeScanner = () => {
  stopScanner()
  showScanner.value = false
}

// 核验二维码
const handleVerify = async () => {
  if (!qrContent.value.trim()) {
    verifyError.value = '请输入二维码内容'
    return
  }

  isVerifying.value = true
  verifyError.value = ''
  verifyResult.value = null

  try {
    const baseURL = import.meta.env.DEV
      ? 'http://localhost:8000/api/v1'
      : (import.meta.env.VITE_API_BASE_URL || 'https://lms.gxj62.cn/api/v1')

    const response = await fetch(`${baseURL}/leaves/verify-qr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ qr_content: qrContent.value.trim() })
    })

    const data = await response.json()
    if (!response.ok) {
      verifyError.value = data.detail || '核验失败'
    } else {
      verifyResult.value = data
    }
  } catch (e: any) {
    verifyError.value = e.message || '网络错误，请稍后重试'
  } finally {
    isVerifying.value = false
  }
}

const goBack = () => {
  router.back()
}

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="verify-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">请假凭证核验</h1>
      </div>

      <div class="verify-card">
        <p class="intro">扫描学生出示的二维码进行核验，或手动输入二维码内容</p>

        <button v-if="!showScanner" @click="startScanner" class="btn btn-primary btn-scan">
          扫描二维码
        </button>

        <div v-if="showScanner" class="scanner-wrapper">
          <div id="qr-scanner" class="scanner-container"></div>
          <button @click="closeScanner" class="btn btn-secondary btn-close-scanner">关闭扫描</button>
        </div>

        <template v-if="!showScanner">
          <textarea
            v-model="qrContent"
            class="qr-input"
            placeholder="请输入二维码内容字符串..."
            rows="4"
          ></textarea>

          <button @click="handleVerify" class="btn btn-primary" :disabled="isVerifying">
            {{ isVerifying ? '核验中...' : '核验' }}
          </button>
        </template>

        <div v-if="verifyError" class="error-message">
          {{ verifyError }}
        </div>

        <div v-if="verifyResult" class="result-card">
          <h3 :class="verifyResult.valid ? 'valid' : 'invalid'">
            {{ verifyResult.valid ? '✅ 核验通过' : '❌ 核验失败' }}
          </h3>

          <div v-if="verifyResult.valid" class="leave-details">
            <div class="detail-row">
              <span class="label">学生姓名：</span>
              <span class="value">{{ verifyResult.student_name || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="label">请假类型：</span>
              <span class="value">{{ verifyResult.leave_type || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="label">请假课时：</span>
              <span class="value">{{ verifyResult.leave_hours || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="label">请假日期：</span>
              <span class="value">{{ formatDate(verifyResult.leave_date) }}</span>
            </div>
            <div class="detail-row">
              <span class="label">审核状态：</span>
              <span class="value status-approved">{{ verifyResult.status }}</span>
            </div>
            <div v-if="verifyResult.audit_remarks" class="detail-row">
              <span class="label">审核意见：</span>
              <span class="value">{{ verifyResult.audit_remarks }}</span>
            </div>
          </div>

          <div v-if="!verifyResult.valid && verifyResult.error_msg" class="error-tip">
            {{ verifyResult.error_msg }}
          </div>
        </div>
      </div>

      <button @click="goBack" class="btn btn-secondary btn-back">返回</button>
    </div>
  </div>
</template>

<style scoped>
.verify-page {
  min-height: 100vh;
  background: var(--bg-secondary);
  padding: var(--spacing-xl) 0;
}

.container {
  max-width: 600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  text-align: center;
}

.verify-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.intro {
  color: var(--text-secondary);
  text-align: center;
  margin: 0;
}

.qr-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  font-size: var(--text-base);
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}

.qr-input:focus {
  outline: none;
  border-color: var(--primary-500);
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius);
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  border: none;
}

.btn-primary {
  background: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-700);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
}

.btn-secondary:hover {
  background: var(--gray-200);
  color: var(--text-primary);
}

.btn-back {
  margin-top: var(--spacing-lg);
  width: 100%;
}

.error-message {
  padding: var(--spacing);
  background: var(--error-light);
  color: var(--error);
  border-radius: var(--radius);
  font-size: var(--text-sm);
}

.result-card {
  padding: var(--spacing-lg);
  background: var(--gray-50);
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
}

.result-card h3 {
  margin: 0 0 var(--spacing-lg) 0;
  font-size: var(--text-lg);
  text-align: center;
}

.result-card h3.valid {
  color: #166534;
}

.result-card h3.invalid {
  color: var(--error);
}

.leave-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--border-light);
}

.detail-row:last-child {
  border-bottom: none;
}

.label {
  font-weight: 500;
  color: var(--text-secondary);
}

.value {
  color: var(--text-primary);
}

.status-approved {
  color: #166534;
  font-weight: 600;
}

.status-rejected {
  color: var(--error);
  font-weight: 600;
}

.error-tip {
  margin-top: var(--spacing);
  padding: var(--spacing);
  background: var(--error-light);
  color: var(--error);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  text-align: center;
}

.btn-scan {
  width: 100%;
  padding: 1rem;
  font-size: var(--text-lg);
}

.scanner-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing);
  margin-bottom: var(--spacing-lg);
}

.scanner-container {
  width: 250px;
  height: 250px;
  border: 2px solid var(--border-medium);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.btn-close-scanner {
  width: 100%;
}

@media (max-width: 480px) {
  .scanner-container {
    width: 200px;
    height: 200px;
  }
}
</style>
