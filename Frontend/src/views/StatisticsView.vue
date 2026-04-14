<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLeaveStatistics, getLeaveTrend, getUserStatistics } from '../api'
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
const leaveStats = ref<any[]>([])
const trendData = ref<any[]>([])
const userStats = ref<any>({})

// 请假状态饼图配置
const pieOption = ref<any>({})

// 请假趋势折线图配置
const lineOption = ref<any>({})

// 用户统计柱状图配置
const barOption = ref<any>({})

const fetchStatistics = async () => {
  try {
    loading.value = true
    const [statsRes, trendRes, userRes] = await Promise.all([
      getLeaveStatistics(),
      getLeaveTrend(30),
      getUserStatistics(),
    ])

    const statsData = statsRes as any
    const trendResponse = trendRes as any
    const userData = userRes as any

    leaveStats.value = statsData?.leave_statistics || []
    trendData.value = trendResponse?.leave_trend || []
    userStats.value = userData?.user_statistics || {}

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
  } catch (error) {
    console.error('获取统计数据失败:', error)
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
  <div class="statistics-page">
    <header class="page-header">
      <div class="container">
        <div class="header-content">
          <button @click="goBack" class="btn btn-outline btn-sm">← 返回</button>
          <h1 class="page-title">数据统计与可视化</h1>
        </div>
      </div>
    </header>

    <main class="page-main">
      <div class="container">
        <div v-if="loading" class="loading-state">
          <p>加载统计数据中...</p>
        </div>

        <div v-else class="charts-grid">
          <div class="chart-card">
            <VChart class="chart" :option="pieOption" autoresize />
          </div>
          <div class="chart-card">
            <VChart class="chart" :option="lineOption" autoresize />
          </div>
          <div class="chart-card">
            <VChart class="chart" :option="barOption" autoresize />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.statistics-page {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--gray-50) 100%);
}

.page-header {
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: var(--spacing) 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--spacing);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-main {
  padding: var(--spacing-xl) 0;
}

.loading-state {
  text-align: center;
  padding: var(--spacing-3xl);
  color: var(--text-tertiary);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--spacing-lg);
}

.chart-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--spacing);
  border: 1px solid var(--border-light);
}

.chart {
  height: 350px;
  width: 100%;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
