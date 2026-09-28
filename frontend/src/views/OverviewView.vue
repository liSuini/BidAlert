<template>
  <div class="overview-view">
    <!-- 指标卡片 -->
    <div class="metrics-row" v-loading="loading">
      <MetricCard label="项目总数" :value="stats.total" type="default" />
      <MetricCard label="正常" :value="stats.normal" type="normal" clickable @click="openProjectsByStatus('normal')" />
      <MetricCard label="预警" :value="stats.warning" type="warning" clickable @click="openProjectsByStatus('warning')" />
      <MetricCard label="超期" :value="stats.overdue" type="overdue" clickable @click="openProjectsByStatus('overdue')" />
      <MetricCard label="已完成" :value="stats.completed" type="completed" clickable @click="openProjectsByStatus('completed')" />
    </div>

    <!-- 图表区 -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">阶段分布</div>
        <div ref="stageChartRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">状态占比</div>
        <div ref="pieChartRef" class="chart-body"></div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">地市分布</div>
        <div ref="regionChartRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">超期项目 TOP 5</div>
        <div class="overdue-list">
          <div v-if="overdueItems.length === 0" class="empty-text">暂无超期项目</div>
          <div v-for="item in overdueItems" :key="item.id" class="overdue-item" @click="openDetail(item.id)" style="cursor: pointer;">
            <span class="overdue-name">{{ item.name }}</span>
            <span class="overdue-stage">{{ item.stage }}</span>
            <span class="overdue-days">超期{{ item.overdue_days }}天</span>
            <span class="overdue-type">{{ overdueTypeLabel(item.overdue_type) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 状态项目列表弹窗 -->
    <el-dialog v-model="statusDialogVisible" :title="statusDialogTitle" width="850px" class="status-dialog">
      <el-table :data="statusDialogData" style="width: 100%" @row-dblclick="openDetail" v-loading="statusDialogLoading" max-height="450">
        <el-table-column prop="name" label="项目名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="region" label="地市" width="90" />
        <el-table-column prop="amount" label="金额(万)" width="90" sortable />
        <el-table-column prop="current_stage" label="当前阶段" width="90" />
        <el-table-column label="已用/剩余" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.days_remaining < 0 ? 'var(--color-overdue)' : '' }">{{ row.days_in_stage }}/{{ row.days_remaining }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_days_used" label="总已用" width="70" sortable />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" link @click="openDetail(row.id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 项目详情弹窗 -->
    <ProjectDetail v-if="detailVisible" :project-id="detailId" @close="detailVisible = false" @updated="loadData" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { statsApi, projectApi } from '../api/stats'
import { projectApi as projectApi2 } from '../api/projects'
import MetricCard from '../components/MetricCard.vue'
import StatusBadge from '../components/StatusBadge.vue'
import ProjectDetail from '../components/ProjectDetail.vue'

const loading = ref(false)
const stats = ref({ total: 0, normal: 0, warning: 0, overdue: 0, completed: 0 })
const overdueItems = ref([])
const stageChartRef = ref(null)
const pieChartRef = ref(null)
const regionChartRef = ref(null)
let stageChart, pieChart, regionChart

// 状态弹窗
const statusDialogVisible = ref(false)
const statusDialogTitle = ref('')
const statusDialogData = ref([])
const statusDialogLoading = ref(false)

// 项目详情弹窗
const detailVisible = ref(false)
const detailId = ref(null)

const overdueTypeLabel = (type) => {
  const map = { stage_overdue: '阶段超期', total_overdue: '总时长超期', both: '双重超期' }
  return map[type] || type
}

const statusColors = { normal: '#3fb950', warning: '#d29922', overdue: '#f85149', completed: '#8b949e' }
const statusLabels = { normal: '正常', warning: '预警', overdue: '超期', completed: '已完成' }

async function openProjectsByStatus(status) {
  statusDialogVisible.value = true
  statusDialogTitle.value = `${statusLabels[status]}项目 (${stats.value[status]}个)`
  statusDialogLoading.value = true
  try {
    const res = await projectApi2.list({ page: 1, size: 100, status })
    statusDialogData.value = res.items
  } catch (e) {
    ElMessage.error('加载项目列表失败')
  } finally {
    statusDialogLoading.value = false
  }
}

function openDetail(id) {
  detailId.value = id
  detailVisible.value = true
}

async function loadData() {
  loading.value = true
  try {
    const [overview, stages, regions, overdue] = await Promise.all([
      statsApi.overview(),
      statsApi.stages(),
      statsApi.regions(),
      statsApi.overdue(5),
    ])
    stats.value = overview
    overdueItems.value = overdue
    await nextTick()
    renderStageChart(stages)
    renderPieChart(overview)
    renderRegionChart(regions)
  } catch (e) {
    console.error('加载统计数据失败:', e)
  } finally {
    loading.value = false
  }
}

function renderStageChart(stages) {
  if (!stageChartRef.value) return
  if (!stageChart) stageChart = echarts.init(stageChartRef.value)
  stageChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['正常', '预警', '超期', '已完成'], textStyle: { color: '#8b949e' }, bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '5%', containLabel: true },
    xAxis: { type: 'category', data: stages.map(s => s.stage), axisLabel: { color: '#8b949e' } },
    yAxis: { type: 'value', axisLabel: { color: '#8b949e' } },
    series: [
      { name: '正常', type: 'bar', stack: 'total', data: stages.map(s => s.normal), itemStyle: { color: statusColors.normal } },
      { name: '预警', type: 'bar', stack: 'total', data: stages.map(s => s.warning), itemStyle: { color: statusColors.warning } },
      { name: '超期', type: 'bar', stack: 'total', data: stages.map(s => s.overdue), itemStyle: { color: statusColors.overdue } },
      { name: '已完成', type: 'bar', stack: 'total', data: stages.map(s => s.completed), itemStyle: { color: statusColors.completed } },
    ],
  })
}

function renderPieChart(overview) {
  if (!pieChartRef.value) return
  if (!pieChart) pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#8b949e' } },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '45%'],
      data: [
        { value: overview.normal, name: '正常', itemStyle: { color: statusColors.normal } },
        { value: overview.warning, name: '预警', itemStyle: { color: statusColors.warning } },
        { value: overview.overdue, name: '超期', itemStyle: { color: statusColors.overdue } },
        { value: overview.completed, name: '已完成', itemStyle: { color: statusColors.completed } },
      ],
      label: { color: '#e6edf3' },
    }],
  })
}

function renderRegionChart(regions) {
  if (!regionChartRef.value) return
  if (!regionChart) regionChart = echarts.init(regionChartRef.value)
  regionChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['正常', '预警', '超期'], textStyle: { color: '#8b949e' }, bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '5%', containLabel: true },
    xAxis: { type: 'category', data: regions.map(r => r.region), axisLabel: { color: '#8b949e' } },
    yAxis: { type: 'value', axisLabel: { color: '#8b949e' } },
    series: [
      { name: '正常', type: 'bar', stack: 'total', data: regions.map(r => r.normal), itemStyle: { color: statusColors.normal } },
      { name: '预警', type: 'bar', stack: 'total', data: regions.map(r => r.warning), itemStyle: { color: statusColors.warning } },
      { name: '超期', type: 'bar', stack: 'total', data: regions.map(r => r.overdue), itemStyle: { color: statusColors.overdue } },
    ],
  })
}

function handleResize() {
  stageChart?.resize()
  pieChart?.resize()
  regionChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  stageChart?.dispose()
  pieChart?.dispose()
  regionChart?.dispose()
})
</script>

<style scoped>
.metrics-row { display: flex; gap: 16px; margin-bottom: 20px; }
.charts-row { display: flex; gap: 16px; margin-bottom: 20px; }
.chart-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px; flex: 1; }
.chart-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: var(--text-primary); }
.chart-body { height: 280px; }
.overdue-list { height: 280px; overflow-y: auto; }
.overdue-item { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--border-color); font-size: 13px; transition: background 0.15s; }
.overdue-item:hover { background: var(--bg-secondary); }
.overdue-name { flex: 1; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.overdue-stage { color: var(--text-secondary); min-width: 80px; }
.overdue-days { color: var(--color-overdue); font-weight: 600; min-width: 70px; text-align: right; }
.overdue-type { color: var(--text-secondary); font-size: 12px; min-width: 80px; text-align: right; }
.empty-text { color: var(--text-secondary); text-align: center; padding: 40px 0; }
</style>
