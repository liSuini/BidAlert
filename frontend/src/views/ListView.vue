<template>
  <div class="list-view">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索项目名称" clearable style="width: 200px" @clear="loadData" @keyup.enter="loadData" />
      <el-select v-model="filterStage" placeholder="阶段" clearable style="width: 140px" @change="loadData">
        <el-option v-for="s in stageOptions" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px" @change="loadData">
        <el-option label="正常" value="normal" />
        <el-option label="预警" value="warning" />
        <el-option label="超期" value="overdue" />
        <el-option label="已完成" value="completed" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button @click="exportData">导出Excel</el-button>
      <el-button type="danger" :disabled="selection.length === 0" @click="batchDelete">
        批量删除{{ selection.length > 0 ? `(${selection.length})` : '' }}
      </el-button>
    </div>

    <!-- 表格 -->
    <el-table :data="tableData" style="width: 100%" v-loading="loading" @row-dblclick="openDetail" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="45" />
      <el-table-column prop="name" label="项目名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="region" label="地市" width="100" />
      <el-table-column prop="amount" label="金额(万)" width="100" sortable />
      <el-table-column prop="bid_subject" label="投标主体" width="100" />
      <el-table-column prop="current_stage" label="当前阶段" width="100" />
      <el-table-column prop="days_in_stage" label="已用天数" width="90" sortable />
      <el-table-column prop="days_remaining" label="剩余天数" width="90" sortable>
        <template #default="{ row }">
          <span :style="{ color: row.days_remaining < 0 ? 'var(--color-overdue)' : '' }">{{ row.days_remaining }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="total_days_used" label="总已用" width="80" sortable />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <StatusBadge :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="openDetail(row.id)">编辑</el-button>
          <el-button size="small" link type="danger" @click="deleteProject(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="size"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      @size-change="loadData"
      @current-change="loadData"
    />

    <ProjectDetail v-if="detailVisible" :project-id="detailId" @close="detailVisible = false" @updated="loadData" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi } from '../api/projects'
import { excelApi } from '../api/excel'
import StatusBadge from '../components/StatusBadge.vue'
import ProjectDetail from '../components/ProjectDetail.vue'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const keyword = ref('')
const filterStage = ref('')
const filterStatus = ref('')
const detailVisible = ref(false)
const detailId = ref(null)
const selection = ref([])

function onSelectionChange(rows) {
  selection.value = rows
}

const stageOptions = ['合同敲定', '合同审批', '业务解构', '合同解析', 'ICT立项', '已完成']

async function loadData() {
  loading.value = true
  try {
    const res = await projectApi.list({
      page: page.value,
      size: size.value,
      keyword: keyword.value || undefined,
      stage: filterStage.value || undefined,
      status: filterStatus.value || undefined,
    })
    tableData.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('加载列表失败:', e)
  } finally {
    loading.value = false
  }
}

function openDetail(id) {
  detailId.value = id
  detailVisible.value = true
}

async function exportData() {
  try {
    const blob = await excelApi.export({
      fields: ['name', 'region', 'responsible_person', 'amount', 'bid_subject',
               'current_stage', 'status', 'overdue_type', 'overdue_stage',
               'days_in_stage', 'days_remaining', 'total_days_used', 'total_days_limit',
               'status_remark'],
      filters: {
        status: filterStatus.value || undefined,
        stage: filterStage.value || undefined,
      },
    })
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = `项目导出_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败:', e)
  }
}

async function deleteProject(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目「${row.name}」吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    await projectApi.delete(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function batchDelete() {
  const count = selection.value.length
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${count} 个项目吗？此操作不可恢复。`,
      '批量删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    let ok = 0, fail = 0
    for (const row of selection.value) {
      try {
        await projectApi.delete(row.id)
        ok++
      } catch {
        fail++
      }
    }
    ElMessage.success(`删除完成：成功 ${ok} 条${fail > 0 ? `，失败 ${fail} 条` : ''}`)
    selection.value = []
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('批量删除失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
</style>
