<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import GenericList from '../components/GenericList.vue'
import { formatDate } from '../utils/formatters'
import { getAllCourses, getStudentCourses, editLeave, approveLeave, rejectLeave, cancelLeave, getLeaveQRCode, closeOffLeave, guaranteeLeave } from '../api'
import http from '../utils/http'
import type { Leave, LeaveCreate, Course, StudentCourseResponse } from '../types'

// 课程列表
const courses = ref<Course[]>([])
const coursesLoading = ref(false)
const listKey = ref(0) // 用于刷新GenericList

// 审核员Tab状态 - 书记/学工处默认显示"全院"，辅导员默认显示"我的"
const reviewerTab = ref<'mine' | 'school'>('school')

// 全院列表（书记/学工处用）
const schoolLeaves = ref<any[]>([])
const schoolLoading = ref(false)
const schoolTotal = ref(0)
const schoolError = ref('')

const fetchSchoolLeaves = async () => {
  if (currentUserRole !== 'reviewer') return
  try {
    schoolLoading.value = true
    schoolError.value = ''
    const res = await http.get('/leaves?page=1&page_size=100&scope=school') as any
    schoolLeaves.value = res?.items || []
    schoolTotal.value = res?.total || 0
  } catch (err: any) {
    schoolError.value = err.message || '获取全院请假失败'
  } finally {
    schoolLoading.value = false
  }
}

// 书记/学工处切换Tab时拉取数据
// const switchTab = (tab: 'mine' | 'school') => {
//   reviewerTab.value = tab
//   if (tab === 'school') {
//     fetchSchoolLeaves()
//   }
// }

// 编辑请假条相关状态
const showEditModal = ref(false)
const isEditing = ref(false)
const editError = ref('')
const currentEditLeave = ref<Leave | null>(null)

// 审核请假条相关状态
const showAuditModal = ref(false)
const isAuditing = ref(false)
const auditError = ref('')
const currentAuditLeave = ref<Leave | null>(null)

// 二维码凭证相关状态
const showQRModal = ref(false)
const qrCodeData = ref('')
const qrLoading = ref(false)
const qrError = ref('')
const auditForm = reactive({
  status: '',
  audit_remarks: ''
})

// 获取当前用户信息
const currentUserId = parseInt(localStorage.getItem('id') || '0')
const currentUserRole = localStorage.getItem('role') || ''

// 页面加载时自动获取全院数据（如果默认显示全院tab）
onMounted(() => {
  if (currentUserRole === 'reviewer' && reviewerTab.value === 'school') {
    fetchSchoolLeaves()
  }
})

// 创建请假条表单数据(用于编辑)
const leaveForm = reactive<LeaveCreate>({
  student_id: currentUserId,
  leave_date: '',
  leave_hours: '',
  status: '待审批',
  leave_type: '',
  remarks: '',
  materials: '',
  course_id: 0,
  teacher_id: 0
})

// 获取课程数据
const fetchCourses = async () => {
  try {
    coursesLoading.value = true

    if (currentUserRole === 'student') {
      const studentCoursesResponse = await getStudentCourses(currentUserId) as unknown as StudentCourseResponse[]

      courses.value = studentCoursesResponse.map((sc: StudentCourseResponse) => ({
        course_id: sc.course_id,
        course_name: sc.course_name || `课程 ${sc.course_id}`,
        class_hours: '0',
        teacher_id: 0,
        teacher_name: sc.teacher_name || '未知教师'
      }))
    } else {
      const response = await getAllCourses() as unknown as { items: Course[] }
      courses.value = response.items || []
    }
  } catch (error) {
    console.error('获取课程失败:', error)
    courses.value = []
  } finally {
    coursesLoading.value = false
  }
}

// 处理课程选择变化
const handleCourseChange = () => {
  leaveForm.teacher_id = 0

  if (leaveForm.course_id && leaveForm.course_id > 0) {
    const selectedCourse = courses.value.find(c => c.course_id === leaveForm.course_id)
    if (selectedCourse) {
      leaveForm.teacher_id = selectedCourse.teacher_id
    }
  }
}

// 打开编辑弹窗
const openEditModal = async (leave: Leave) => {
  showEditModal.value = true
  editError.value = ''
  currentEditLeave.value = leave

  await fetchCourses()

  Object.assign(leaveForm, {
    student_id: leave.student_id,
    leave_date: leave.leave_date ? new Date(leave.leave_date).toISOString().split('T')[0] : '',
    leave_hours: leave.leave_hours || '',
    leave_type: leave.leave_type || '',
    remarks: leave.remarks || '',
    materials: leave.materials || '',
    course_id: leave.course_id || 0,
    teacher_id: leave.teacher_id || 0
  })
}

// 关闭编辑弹窗
const closeEditModal = () => {
  showEditModal.value = false
  editError.value = ''
  currentEditLeave.value = null
}

// 处理编辑请假条
const handleEditLeave = async () => {
  try {
    isEditing.value = true
    editError.value = ''

    if (!currentEditLeave.value) return

    if (!leaveForm.student_id || !leaveForm.leave_date || !leaveForm.leave_hours) {
      editError.value = '请填写必填字段：学生ID、请假日期、请假课时'
      return
    }

    const formattedData: any = {
      student_id: parseInt(leaveForm.student_id.toString()),
      leave_date: leaveForm.leave_date,
      leave_hours: leaveForm.leave_hours ? leaveForm.leave_hours.toString() : '',
    }

    if (leaveForm.course_id && leaveForm.course_id > 0) {
      formattedData.course_id = parseInt(leaveForm.course_id.toString())

      const selectedCourse = courses.value.find(c => c.course_id === leaveForm.course_id)
      if (selectedCourse) {
        formattedData.teacher_id = selectedCourse.teacher_id
      }
    }

    if (leaveForm.leave_type) {
      formattedData.leave_type = leaveForm.leave_type.slice(0, 8)
    }
    if (leaveForm.remarks) {
      formattedData.remarks = leaveForm.remarks.slice(0, 100)
    }
    if (leaveForm.materials) {
      formattedData.materials = leaveForm.materials.slice(0, 100)
    }

    await editLeave(currentEditLeave.value.leave_id, formattedData)

    closeEditModal()
    listKey.value++

  } catch (error: any) {
    console.error('编辑请假条失败:', error)

    let errorMessage = '编辑失败，请重试'
    if (error.response?.data) {
      const errorData = error.response.data
      if (errorData.detail && Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail.map((item: any) => `${item.loc?.join('.')}: ${item.msg}`).join('; ')
      } else if (errorData.message) {
        errorMessage = errorData.message
      } else if (typeof errorData === 'string') {
        errorMessage = errorData
      }
    }

    editError.value = errorMessage
  } finally {
    isEditing.value = false
  }
}

// 打开审核弹窗
const openAuditModal = (leave: Leave) => {
  showAuditModal.value = true
  auditError.value = ''
  currentAuditLeave.value = leave

  Object.assign(auditForm, {
    status: '',
    audit_remarks: ''
  })
}

// 关闭审核弹窗
const closeAuditModal = () => {
  showAuditModal.value = false
  auditError.value = ''
  currentAuditLeave.value = null
  Object.assign(auditForm, {
    status: '',
    audit_remarks: ''
  })
}

// 处理审核请假条 - 使用专用approve/reject API
const handleAuditLeave = async () => {
  try {
    isAuditing.value = true
    auditError.value = ''

    if (!currentAuditLeave.value) return

    if (!auditForm.status) {
      auditError.value = '请选择审核状态'
      return
    }

    const remarks = auditForm.audit_remarks ? auditForm.audit_remarks.slice(0, 100) : ''

    if (auditForm.status === '已批准') {
      await approveLeave(currentAuditLeave.value.leave_id, remarks)
    } else if (auditForm.status === '已拒绝') {
      await rejectLeave(currentAuditLeave.value.leave_id, remarks)
    }

    closeAuditModal()
    listKey.value++

  } catch (error: any) {
    console.error('审核请假条失败:', error)

    let errorMessage = '审核失败，请重试'
    if (error.response?.data) {
      const errorData = error.response.data
      if (errorData.detail && Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail.map((item: any) => `${item.loc?.join('.')}: ${item.msg}`).join('; ')
      } else if (errorData.message) {
        errorMessage = errorData.message
      } else if (typeof errorData === 'string') {
        errorMessage = errorData
      }
    }

    auditError.value = errorMessage
  } finally {
    isAuditing.value = false
  }
}

// 撤销请假条
const handleCancelLeave = async (leave: Leave) => {
  if (!confirm('确定要撤销这条请假申请吗？')) return

  try {
    await cancelLeave(leave.leave_id)
    listKey.value++
  } catch (error: any) {
    console.error('撤销请假条失败:', error)
    alert(error.response?.data?.detail || '撤销失败')
  }
}

// 销假 - 辅导员确认学生已返校报到
const handleCloseOff = async (leave: Leave) => {
  const isGuarantor = leave.guarantee_student_id === currentUserId && leave.student_id !== currentUserId
  let penaltyDays: number | undefined

  if (isGuarantor) {
    // 担保人操作销假，可选择惩罚天数
    const confirmText = `确定要对该请假执行销假操作吗？\n学生: ${leave.student_name}\n类型: ${leave.leave_type}\n课时: ${leave.leave_hours}\n\n是否对双方学生进行处罚？`
    const userConfirm = confirm(confirmText + '\n\n点确定：处罚7天\n点取消：仅销假')

    if (userConfirm) {
      penaltyDays = 7
    } else {
      penaltyDays = undefined
    }
  } else {
    if (!confirm(`确定要对该请假执行销假操作吗？\n学生: ${leave.student_name}\n类型: ${leave.leave_type}\n课时: ${leave.leave_hours}`)) return
  }

  try {
    await closeOffLeave(leave.leave_id, penaltyDays)
    listKey.value++
  } catch (error: any) {
    console.error('销假失败:', error)
    alert(error.response?.data?.detail || '销假失败')
  }
}

// 担保请假条
const handleGuarantee = async (leave: Leave) => {
  if (!confirm(`确定要担保这张请假条吗？\n学生: ${leave.student_name}\n类型: ${leave.leave_type}\n课时: ${leave.leave_hours}`)) return

  try {
    await guaranteeLeave(leave.leave_id)
    alert('担保成功，请假条已生效')
    listKey.value++
  } catch (error: any) {
    console.error('担保失败:', error)
    alert(error.response?.data?.detail || '担保失败')
  }
}

// 判断是否为该学生的担保人
const isGuarantorFor = (leave: Leave): boolean => {
  return leave.guarantee_student_id === currentUserId && leave.student_id !== currentUserId
}

// 判断是否可以编辑（学生只能编辑自己的待审批请假条）
const canEdit = (leave: Leave): boolean => {
  return currentUserRole === 'student' && leave.student_id === currentUserId && leave.status === '待审批'
}

// 判断是否可以审核（审核员/管理员可以审核待审批的请假条）
const canAudit = (leave: Leave): boolean => {
  if (currentUserRole === 'admin')
    return true
  else if (currentUserRole === 'reviewer' && leave.status === '待审批')
    return true
  else return false
}

// 判断是否可以撤销（学生可以撤销自己的待审批请假条）
const canCancel = (leave: Leave): boolean => {
  return (currentUserRole === 'student' && leave.student_id === currentUserId && leave.status === '待审批') ||
    currentUserRole === 'admin'
}

// 判断是否可以销假（辅导员/书记/管理员可以对已批准的请假执行销假）
const canCloseOff = (leave: Leave): boolean => {
  return leave.status === '已批准' && (currentUserRole === 'reviewer' || currentUserRole === 'admin')
}

// 展示二维码凭证
const showQRCode = async (leave: Leave) => {
  showQRModal.value = true
  qrCodeData.value = ''
  qrError.value = ''
  qrLoading.value = true

  try {
    const response = await getLeaveQRCode(leave.leave_id) as any
    if (response.error) {
      qrError.value = response.error
    } else {
      qrCodeData.value = response.qr_code
    }
  } catch (error: any) {
    qrError.value = error.response?.data?.detail || '获取二维码失败'
  } finally {
    qrLoading.value = false
  }
}

const closeQRModal = () => {
  showQRModal.value = false
  qrCodeData.value = ''
  qrError.value = ''
}

// 判断是否可以下载证明材料
const canDownloadMaterials = (leave: Leave): boolean => {
  return !!(leave.materials && leave.materials.trim())
}

// 下载证明材料
const downloadMaterials = (leave: Leave) => {
  if (!leave.materials) return
  const files = leave.materials.split(',').filter((f: string) => f.trim())
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  files.forEach((fileName: string) => {
    const trimmed = fileName.trim()
    if (!trimmed) return
    // 提取 leave_id 和文件名
    // materials 格式: uploads/{leave_id}/{filename}
    const parts = trimmed.split('/')
    const filename = parts[parts.length - 1]
    const leaveId = leave.leave_id
    const url = `${apiBase}/leaves/${leaveId}/download/${encodeURIComponent(filename)}`
    window.open(url, '_blank')
  })
}

// 格式化材料字段为可点击链接
const formatMaterials = (value: string): string => {
  if (!value || !value.trim()) return '-'
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  return value.split(',').map((f: string) => f.trim()).filter(Boolean).map(fileName => {
    const parts = fileName.split('/')
    const filename = parts[parts.length - 1]
    const leaveId = parts.length >= 2 ? parts[parts.length - 2] : ''
    return `<a href="${apiBase}/leaves/${leaveId}/download/${encodeURIComponent(filename)}" target="_blank" class="material-link">${filename}</a>`
  }).join('<br>')
}

</script>

<template>
  <div class="leaves-page">
    <!-- 审核员视图 -->
    <GenericList v-if="currentUserRole === 'reviewer'" :key="listKey" endpoint="/leaves" title="请假条列表" item-label="张请假条" :show-actions="true" :show-create="false"
      :columns="[
        { key: 'leave_id', label: '请假ID' },
        { key: 'student_name', label: '学生名称' },
        { key: 'leave_type', label: '请假类型' },
        { key: 'leave_hours', label: '请假课时' },
        {
          key: 'leave_date',
          label: '请假时间',
          formatter: formatDate
        },
        { key: 'remarks', label: '备注' },
        {
          key: 'status',
          label: '状态'
        },
        { key: 'reviewer_name', label: '审核人姓名' },
        { key: 'audit_remarks', label: '审核意见' },
        {
          key: 'materials',
          label: '证明材料',
          formatter: formatMaterials
        }
      ]">
      <template #actions="{ item }">
        <div class="action-buttons">
          <button v-if="canEdit(item)" @click="openEditModal(item)" class="btn btn-warning btn-sm">
            修改
          </button>
          <button v-if="canAudit(item)" @click="openAuditModal(item)" class="btn btn-primary btn-sm">
            审核
          </button>
          <button v-if="canCancel(item)" @click="handleCancelLeave(item)" class="btn btn-danger btn-sm">
            撤销
          </button>
          <button v-if="canCloseOff(item)" @click="handleCloseOff(item)" class="btn btn-success btn-sm">
            销假
          </button>
          <button v-if="canDownloadMaterials(item)" @click="downloadMaterials(item)" class="btn btn-info btn-sm">
            下载材料
          </button>
        </div>
      </template>
    </GenericList>

    <!-- 学生视图 -->
    <GenericList v-else-if="currentUserRole === 'student'" :key="listKey" endpoint="/leaves" title="我的请假条" item-label="张请假条" :show-actions="true" :show-create="true" create-type="leave"
      :columns="[
        { key: 'leave_id', label: '请假ID' },
        { key: 'leave_type', label: '请假类型' },
        { key: 'leave_hours', label: '请假课时' },
        {
          key: 'leave_date',
          label: '请假时间',
          formatter: formatDate
        },
        { key: 'remarks', label: '备注' },
        {
          key: 'status',
          label: '状态'
        },
        {
          key: 'guarantee_student_name',
          label: '担保人'
        },
        { key: 'reviewer_name', label: '审核人姓名' },
        { key: 'audit_remarks', label: '审核意见' },
        { key: 'materials', label: '证明材料' }
      ]">
      <template #actions="{ item }">
        <div class="action-buttons">
          <button v-if="canEdit(item)" @click="openEditModal(item)" class="btn btn-warning btn-sm">
            修改
          </button>
          <button v-if="canCancel(item)" @click="handleCancelLeave(item)" class="btn btn-danger btn-sm">
            撤销
          </button>
          <button v-if="isGuarantorFor(item) && item.status === '待审批'" @click="handleGuarantee(item)" class="btn btn-primary btn-sm">
            担保
          </button>
          <button v-if="item.status === '已批准'" @click="showQRCode(item)" class="btn btn-info btn-sm">
            查看凭证
          </button>
        </div>
      </template>
    </GenericList>

    <!-- 管理员视图 -->
    <GenericList v-else-if="currentUserRole === 'admin'" :key="listKey" endpoint="/leaves" title="请假条列表" item-label="张请假条" :show-actions="true" :show-create="false"
      :columns="[
        { key: 'leave_id', label: '请假ID' },
        { key: 'student_name', label: '学生名称' },
        { key: 'leave_type', label: '请假类型' },
        { key: 'leave_hours', label: '请假课时' },
        {
          key: 'leave_date',
          label: '请假时间',
          formatter: formatDate
        },
        { key: 'remarks', label: '备注' },
        {
          key: 'status',
          label: '状态'
        },
        { key: 'reviewer_name', label: '审核人姓名' },
        { key: 'audit_remarks', label: '审核意见' },
        {
          key: 'materials',
          label: '证明材料',
          formatter: formatMaterials
        }
      ]">
      <template #actions="{ item }">
        <div class="action-buttons">
          <button v-if="canAudit(item)" @click="openAuditModal(item)" class="btn btn-primary btn-sm">
            审核
          </button>
          <button v-if="item.status === '已批准'" @click="showQRCode(item)" class="btn btn-info btn-sm">
            查看凭证
          </button>
          <button v-if="canCloseOff(item)" @click="handleCloseOff(item)" class="btn btn-success btn-sm">
            销假
          </button>
          <button v-if="canDownloadMaterials(item)" @click="downloadMaterials(item)" class="btn btn-info btn-sm">
            下载材料
          </button>
        </div>
      </template>
    </GenericList>

    <!-- 教师视图 -->
    <GenericList v-else-if="currentUserRole === 'teacher'" :key="listKey" endpoint="/leaves" title="请假条列表" item-label="张请假条" :show-actions="true" :show-create="false"
      :columns="[
        { key: 'leave_id', label: '请假ID' },
        { key: 'student_name', label: '学生名称' },
        { key: 'leave_type', label: '请假类型' },
        { key: 'leave_hours', label: '请假课时' },
        {
          key: 'leave_date',
          label: '请假时间',
          formatter: formatDate
        },
        { key: 'remarks', label: '备注' },
        {
          key: 'status',
          label: '状态'
        },
        { key: 'reviewer_name', label: '审核人姓名' },
        { key: 'audit_remarks', label: '审核意见' },
        {
          key: 'materials',
          label: '证明材料',
          formatter: formatMaterials
        }
      ]">
      <template #actions="{ item }">
        <div class="action-buttons">
          <button v-if="item.status === '已批准'" @click="showQRCode(item)" class="btn btn-info btn-sm">
            查看凭证
          </button>
          <button v-if="canDownloadMaterials(item)" @click="downloadMaterials(item)" class="btn btn-info btn-sm">
            下载材料
          </button>
        </div>
      </template>
    </GenericList>

    <!-- 编辑请假条弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>修改请假条</h3>
        </div>

        <form @submit.prevent="handleEditLeave" class="modal-form">
          <div class="form-row-two">
            <div class="form-group">
              <label for="edit_student_id">
                学生ID
              </label>
              <input type="number" id="edit_student_id" v-model="leaveForm.student_id" readonly disabled
                class="readonly-input" :placeholder="`当前用户ID: ${currentUserId}`" min="1" />
            </div>
            <div class="form-group">
              <label for="edit_leave_date">请假日期 *</label>
              <input type="date" id="edit_leave_date" v-model="leaveForm.leave_date" required />
            </div>
          </div>

          <div class="form-group">
            <label for="edit_course">课程</label>
            <select id="edit_course" v-model="leaveForm.course_id" @change="handleCourseChange">
              <option value="0">请选择课程</option>
              <option v-if="coursesLoading" value="">加载中...</option>
              <option v-for="course in courses" :key="course.course_id" :value="course.course_id">
                {{ course.course_name }} ({{ course.teacher_name }})
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="edit_leave_hours">请假课时 *</label>
              <input type="number" id="edit_leave_hours" v-model="leaveForm.leave_hours" required placeholder="数字" />
            </div>
            <div class="form-group">
              <label for="edit_leave_type">请假类型</label>
              <select id="edit_leave_type" v-model="leaveForm.leave_type">
                <option value="">请选择请假类型</option>
                <option value="病假">病假</option>
                <option value="事假">事假</option>
                <option value="公假">公假</option>
                <option value="其他">其他</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="edit_remarks">备注</label>
            <textarea id="edit_remarks" v-model="leaveForm.remarks" rows="3" placeholder="请输入请假事由等备注信息"
              maxlength="100"></textarea>
          </div>

          <div v-if="editError" class="error-message">
            {{ editError }}
          </div>

          <div class="modal-footer">
            <button type="button" @click="closeEditModal" class="btn btn-secondary">
              取消
            </button>
            <button type="submit" class="btn btn-primary" :disabled="isEditing">
              {{ isEditing ? '修改中...' : '确认修改' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 审核请假条弹窗 -->
    <div v-if="showAuditModal" class="modal-overlay" @click.self="closeAuditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>审核请假条</h3>
        </div>

        <form @submit.prevent="handleAuditLeave" class="modal-form">
          <div class="form-group">
            <label for="audit_status">审核状态 *</label>
            <select id="audit_status" v-model="auditForm.status" required>
              <option value="">请选择审核状态</option>
              <option value="已批准">已批准</option>
              <option value="已拒绝">已拒绝</option>
            </select>
          </div>

          <div class="form-group">
            <label for="audit_remarks">审核备注</label>
            <textarea id="audit_remarks" v-model="auditForm.audit_remarks" rows="4" placeholder="请输入审核意见"
              maxlength="100"></textarea>
          </div>

          <div v-if="auditError" class="error-message">
            {{ auditError }}
          </div>

          <div class="modal-footer">
            <button type="button" @click="closeAuditModal" class="btn btn-secondary">
              取消
            </button>
            <button type="submit" class="btn btn-primary" :disabled="isAuditing">
              {{ isAuditing ? '审核中...' : '确认审核' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 二维码凭证弹窗 -->
    <div v-if="showQRModal" class="modal-overlay" @click.self="closeQRModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>请假凭证</h3>
        </div>
        <div class="qr-container">
          <div v-if="qrLoading" class="qr-loading">加载中...</div>
          <div v-else-if="qrError" class="error-message">{{ qrError }}</div>
          <div v-else-if="qrCodeData" class="qr-display">
            <img :src="'data:image/png;base64,' + qrCodeData" alt="请假凭证二维码" class="qr-image" />
            <p class="qr-hint">请将此二维码出示给教师核验</p>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" @click="closeQRModal" class="btn btn-secondary">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 弹窗样式 */
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
  padding: var(--spacing);
}

.modal-content {
  background-color: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  max-width: 600px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-form {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.form-row-two {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  font-size: var(--text-base);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: all var(--transition);
  height: 2.75rem;
  line-height: 1.5;
  box-sizing: border-box;
}

.form-group input[type="date"] {
  height: 2.75rem;
  padding: 0.5rem 0.75rem;
}

.form-group select {
  height: 2.75rem;
  padding: 0.5rem 0.75rem;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
  padding-right: 2.5rem;
}

.form-group textarea {
  height: auto;
  min-height: 80px;
  resize: vertical;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
}

.readonly-input {
  background-color: var(--gray-100);
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.error-message {
  background-color: var(--error-light);
  color: var(--error);
  padding: var(--spacing);
  border-radius: var(--radius);
  border: 1px solid #fca5a5;
  font-size: var(--text-sm);
  font-weight: 500;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing);
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-light);
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: var(--spacing-sm);
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: var(--text-sm);
}

.btn-warning {
  background-color: #f59e0b;
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-warning:hover {
  background-color: #d97706;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-danger {
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-danger:hover {
  background-color: #dc2626;
}

.btn-secondary {
  background-color: var(--gray-100);
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-weight: 500;
  transition: all var(--transition);
}

.btn-secondary:hover {
  background-color: var(--gray-200);
  color: var(--text-primary);
  border-color: var(--border-dark);
}

.btn-info {
  background-color: var(--info, #0ea5e9);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-info:hover {
  background-color: #0284c7;
}

.btn-success {
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-success:hover {
  background-color: #059669;
}

.qr-container {
  padding: var(--spacing-lg);
  text-align: center;
}

.qr-loading {
  padding: 2rem;
  color: var(--text-secondary);
}

.qr-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing);
}

.qr-image {
  max-width: 250px;
  max-height: 250px;
  border: 2px solid var(--border-medium);
  border-radius: var(--radius);
  padding: var(--spacing);
  background: white;
}

.qr-hint {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .modal-content {
    max-width: 90%;
  }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-content {
    max-width: 100%;
    margin: var(--spacing);
  }

  .modal-header {
    padding: var(--spacing);
  }

  .modal-form {
    padding: var(--spacing);
  }

  .modal-footer {
    flex-direction: column;
  }

  .modal-footer button {
    width: 100%;
  }
}

/* 审核员Tab切换 */
.reviewer-tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}

.tab-btn {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: var(--radius);
  background: transparent;
  color: var(--text-secondary);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.tab-btn:hover {
  background: var(--gray-50);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--primary-600);
  color: white;
}

.material-link {
  color: var(--primary-600, #2563eb);
  text-decoration: underline;
  cursor: pointer;
}

.material-link:hover {
  color: var(--primary-700, #1d4ed8);
}
</style>
