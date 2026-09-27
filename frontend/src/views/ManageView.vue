<template>
  <div class="manage-view">
    <!-- 导入区 -->
    <div class="section-card">
      <div class="section-title">Excel 导入</div>
      <div class="import-area">
        <el-upload
          :show-file-list="false"
          accept=".xlsx,.xls"
          :http-request="handleImport"
        >
          <el-button type="primary">上传 Excel 文件</el-button>
        </el-upload>
        <el-button @click="downloadTemplate">下载导入模板</el-button>
      </div>
      <div v-if="importResult" class="import-result">
        <el-alert :type="importResult.failed > 0 ? 'warning' : 'success'" :closable="false">
          共 {{ importResult.total }} 条，成功 {{ importResult.success }} 条，失败 {{ importResult.failed }} 条
        </el-alert>
        <div v-if="importResult.fail_details?.length" class="fail-details">
          <div v-for="(d, i) in importResult.fail_details" :key="i" class="fail-item">
            第{{ d.row }}行：{{ d.reason }}
          </div>
        </div>
      </div>
    </div>

    <!-- 导出区 -->
    <div class="section-card">
      <div class="section-title">Excel 导出</div>
      <div class="export-fields">
        <el-checkbox v-model="exportFields" v-for="f in allFields" :key="f.key" :label="f.key">{{ f.label }}</el-checkbox>
      </div>
      <div class="export-actions">
        <el-button @click="selectAllFields">全选</el-button>
        <el-button @click="exportFields = []">反选</el-button>
        <el-button type="primary" @click="exportAll">导出全部</el-button>
      </div>
    </div>

    <!-- 手动新增 -->
    <div class="section-card">
      <div class="section-title">手动新增项目</div>
      <el-button type="primary" @click="showAddForm = true">新增项目</el-button>
    </div>

    <!-- 新增表单弹窗 -->
    <el-dialog v-model="showAddForm" title="新增项目" width="600px">
      <el-form :model="addForm" label-width="140px">
        <el-form-item label="项目名称"><el-input v-model="addForm.name" /></el-form-item>
        <el-form-item label="地市/部门"><el-input v-model="addForm.region" /></el-form-item>
        <el-form-item label="责任人"><el-input v-model="addForm.responsible_person" /></el-form-item>
        <el-form-item label="项目金额(万)"><el-input-number v-model="addForm.amount" :min="0" /></el-form-item>
        <el-form-item label="投标主体">
          <el-select v-model="addForm.bid_subject">
            <el-option label="信产" value="信产" />
            <el-option label="数智" value="数智" />
          </el-select>
        </el-form-item>
        <el-form-item label="中标通知书日期"><el-date-picker v-model="addForm.bid_notice_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddForm = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { excelApi } from '../api/excel'
import { projectApi } from '../api/projects'

const importResult = ref(null)
const showAddForm = ref(false)
const addForm = ref({ name: '', region: '', responsible_person: '', amount: 0, bid_subject: '信产', bid_notice_date: '' })

const allFields = [
  { key: 'name', label: '项目名称' },
  { key: 'region', label: '地市/部门' },
  { key: 'responsible_person', label: '责任人' },
  { key: 'amount', label: '项目金额' },
  { key: 'bid_subject', label: '投标主体' },
  { key: 'current_stage', label: '当前阶段' },
  { key: 'status', label: '状态' },
  { key: 'overdue_type', label: '超期类型' },
  { key: 'days_in_stage', label: '已用天数' },
  { key: 'days_remaining', label: '剩余天数' },
  { key: 'total_days_used', label: '总已用' },
  { key: 'total_days_limit', label: '总时限' },
  { key: 'status_remark', label: '情况说明' },
]
const exportFields = ref(['name', 'region', 'amount', 'current_stage', 'status', 'days_in_stage', 'total_days_used'])

function selectAllFields() { exportFields.value = allFields.map(f => f.key) }

async function handleImport({ file }) {
  try {
    const result = await excelApi.import(file)
    importResult.value = result
    ElMessage.success(`导入完成：成功${result.success}条，失败${result.failed}条`)
  } catch (e) {
    ElMessage.error('导入失败')
  }
}

async function downloadTemplate() {
  try {
    const blob = await excelApi.getTemplate()
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = '项目导入模板.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('下载模板失败')
  }
}

async function exportAll() {
  try {
    const blob = await excelApi.export({ fields: exportFields.value, filters: {} })
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = `项目导出_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

async function handleAdd() {
  if (!addForm.value.name) { ElMessage.warning('请填写项目名称'); return }
  try {
    await projectApi.create(addForm.value)
    ElMessage.success('新增成功')
    showAddForm.value = false
    addForm.value = { name: '', region: '', responsible_person: '', amount: 0, bid_subject: '信产', bid_notice_date: '' }
  } catch (e) {
    ElMessage.error('新增失败')
  }
}
</script>

<style scoped>
.section-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.section-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.import-area { display: flex; gap: 12px; }
.import-result { margin-top: 16px; }
.fail-details { margin-top: 8px; max-height: 200px; overflow-y: auto; }
.fail-item { color: var(--color-overdue); font-size: 13px; padding: 4px 0; }
.export-fields { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.export-actions { display: flex; gap: 8px; }
</style>
