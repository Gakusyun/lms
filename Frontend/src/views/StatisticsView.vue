<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getLeaveStatistics, getLeaveTrend, getUserStatistics, getReviewerStudentsStatistics } from '../api'
import { getUserInfo } from '../utils/auth'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'

use([
  CanvasRenderer,
  PieChart,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const router = useRouter()
const loading = ref(true)
const error = ref('')
const leaveStats = ref<any[]>([])
const trendData = ref<any[]>([])
const userStats = ref<any>({})
const reviewerStudentsStats = ref<any[]>([])

// 获取用户信息
const userInfo = computed(() => getUserInfo())

// 请假状态饼图配置
const pieOption = ref<any>({})

// 请假趋势折线图配置
const lineOption = ref<any>({})

// 用户统计柱状图配置
const barOption = ref<any>({})

const fetchStatistics = async () => {
  try {
    loading.value = true
    error.value = ''
    
    // 根据用户角色决定调用哪些API
    const requests = [
      getLeaveStatistics(),
      getLeaveTrend(30)
    ]
    
    // 只有管理员可以查看用户统计
    if (userInfo.value?.role === 'admin') {
      requests.push(getUserStatistics())
    }
    
    // 只有审核员可以查看自己管理的学生统计
    if (userInfo.value?.role === 'reviewer') {
      requests.push(getReviewerStudentsStatistics())
    }
    
    const responses = await Promise.all(requests)
    
    // 处理响应
    let statsData = responses[0] as any
    let trendResponse = responses[1] as any
    let userData: any = {}
    let reviewerStudentsData: any = {}
    
    // 根据用户角色和响应长度处理数据
    if (userInfo.value?.role === 'admin' && responses.length >= 3) {
      userData = responses[2] as any
    }
    
    // 检查是否需要处理审核员学生统计数据
    const isReviewer = userInfo.value?.role === 'reviewer'
    const hasReviewerData = isReviewer && responses.length >= (userInfo.value?.role === 'admin' ? 4 : 3)
    
    if (hasReviewerData) {
      const reviewerDataIndex = userInfo.value?.role === 'admin' ? 3 : 2
      reviewerStudentsData = responses[reviewerDataIndex] as any
    }

    leaveStats.value = statsData?.leave_statistics || []
    trendData.value = trendResponse?.leave_trend || []
    userStats.value = userData?.user_statistics || {}
    reviewerStudentsStats.value = reviewerStudentsData?.students_statistics || []

    // 饼图
    pieOption.value = {
      title: { text: '请假状态分布', left: 'center' },
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 20, fontWeight: 'bold' }
        },
        data: leaveStats.value.map((item: any) => ({
          name: item.status,
          value: item.count,
        })),
      }],
    }

    // 折线图
    const trend = (trendResponse as any)?.leave_trend || []
    lineOption.value = {
      title: { text: '近30天请假趋势', left: 'center' },
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: trend.map((item: any) => item.date?.substring(5, 10)),
      },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{
        name: '请假次数',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3 },
        data: trend.map((item: any) => item.count),
      }],
    }

    // 柱状图
    barOption.value = {
      title: { text: '用户统计', left: 'center' },
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: ['学生', '教师', '审核员'],
      },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{
        name: '人数',
        type: 'bar',
        barWidth: '60%',
        itemStyle: { borderRadius: [5, 5, 0, 0] },
        data: [
          userStats.value.students || 0,
          userStats.value.teachers || 0,
          userStats.value.reviewers || 0,
        ],
      }],
    }
  } catch (err: any) {
    error.value = err.message || '获取统计数据失败'
    console.error('获取统计数据失败:', err)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  fetchStatistics()
})
</script>

<template>
  <div class="list-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">数据统计与可视化</h1>
        <div class="header-buttons">
          <button @click="goBack" class="btn btn-back">返回首页</button>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <span>正在加载统计数据...</span>
      </div>

      <div v-else-if="error" class="error">
        <span>{{ error }}</span>
      </div>

      <div v-else class="page-content">
        <div class="stats-card">
          <p class="stats-text">系统数据统计概览</p>
        </div>

        <div class="charts-grid">
          <div class="chart-card">
            <VChart class="chart" :option="pieOption" autoresize />
          </div>
          <div class="chart-card">
            <VChart class="chart" :option="lineOption" autoresize />
          </div>
          <div v-if="userInfo?.role === 'admin'" class="chart-card">
            <VChart class="chart" :option="barOption" autoresize />
          </div>
        </div>

        <!-- 审核员学生统计表格 -->
        <div v-if="userInfo?.role === 'reviewer'" class="stats-card">
          <h3 class="stats-title">管理学生请假统计</h3>
          <div class="table-container">
            <table class="stats-table">
              <thead>
                <tr>
                  <th>学生ID</th>
                  <th>学生姓名</th>
                  <th>请假总数</th>
                  <th>已批准</th>
                  <th>已拒绝</th>
                  <th>待审批</th>
                  <th>批准率</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="student in reviewerStudentsStats" :key="student.student_id">
                  <td>{{ student.student_id }}</td>
                  <td>{{ student.student_name }}</td>
                  <td>{{ student.total_leaves }}</td>
                  <td>{{ student.approved_leaves }}</td>
                  <td>{{ student.rejected_leaves }}</td>
                  <td>{{ student.pending_leaves }}</td>
                  <td>{{ student.approval_rate }}%</td>
                </tr>
                <tr v-if="reviewerStudentsStats.length === 0">
                  <td colspan="7" class="empty-state">暂无学生数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-page {
  min-height: 100vh;
  background-color: var(--bg-secondary);
  padding: var(--spacing-lg) 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing);
  border-bottom: 1px solid var(--border-light);
}

.header-buttons {
  display: flex;
  gap: var(--spacing);
}

.page-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.stats-card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing);
  box-shadow: var(--shadow);
}

.stats-text {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
  font-weight: 500;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--text-secondary);
  gap: var(--spacing);
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--border-light);
  border-top: 2px solid var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--error);
  background-color: var(--error-light);
  border: 1px solid #fca5a5;
  border-radius: var(--radius-lg);
  font-weight: 500;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--spacing-lg);
}

.chart-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  padding: var(--spacing);
}

.chart {
  height: 350px;
  width: 100%;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  font-size: var(--text-sm);
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
  border-color: var(--border-dark);
}

.stats-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing) 0;
}

.table-container {
  overflow-x: auto;
  margin-top: var(--spacing);
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.stats-table th,
.stats-table td {
  padding: var(--spacing-sm);
  text-align: left;
  border-bottom: 1px solid var(--border-light);
}

.stats-table th {
  background-color: var(--bg-secondary);
  font-weight: 600;
  color: var(--text-primary);
}

.stats-table tr:hover {
  background-color: var(--bg-secondary);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--text-secondary);
  font-style: italic;
}

@media (max-width: 768px) {
  .list-page {
    padding: var(--spacing) 0;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing);
  }

  .page-title {
    font-size: var(--text-2xl);
    text-align: center;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
