<template>
  <el-dialog :model-value="true" @close="$emit('close')" title="项目详情" width="800px" class="detail-dialog">
    <div v-loading="loading">
      <!-- 基本信息（可编辑） -->
      <div class="detail-section">
        <div class="section-title">基本信息</div>
        <div class="info-form">
          <div class="form-row">
            <label>项目名称</label>
            <el-input v-model="editForm.name" size="small" />
          </div>
          <div class="form-grid">
            <div class="form-row">
              <label>地市/部门</label>
              <el-input v-model="editForm.region" size="small" />
            </div>
            <div class="form-row">
              <label>责任人</label>
              <el-input v-model="editForm.responsible_person" size="small" />
            </div>
            <div class="form-row">
              <label>项目金额(万)</label>
              <el-input-number v-model="editForm.amount" :min="0" :controls="false" size="small" style="width: 100%" />
            </div>
            <div class="form-row">
              <label>投标主体</label>
              <el-select v-model="editForm.bid_subject" size="small" style="width: 100%">
                <el-option label="信产" value="信产" />
                <el-option label="数智" value="数智" />
              </el-select>
            </div>
          </div>
          <div class="form-row" style="margin-top: 4px;">
            <label>状态</label>
            <div style="padding-top: 4px;"><StatusBadge :status="detail.status" /></div>
          </div>
          <el-button type="primary" size="small" @click="saveBasic" style="margin-top: 8px;">保存基本信息</el-button>
        </div>
      </div>

      <!-- 阶段时间线 -->
      <div class="detail-section">
        <div class="section-title">阶段时间线</div>
        <div class="timeline">
          <div v-for="item in detail.stage_timeline" :key="item.stage" class="timeline-item" :class="item.status">
            <div class="timeline-stage">{{ item.stage }}</div>
            <div class="timeline-bar">
              <div class="bar-fill" :style="{ width: Math.min(item.days_used / item.limit * 100, 100) + '%' }"></div>
            </div>
            <div class="timeline-info">
              <span>{{ item.days_used }}/{{ item.limit }}天</span>
              <span v-if="item.start" class="timeline-date">{{ item.start }} → {{ item.end || '进行中' }}</span>
              <span v-else class="timeline-date">待开始</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 状态统计 -->
      <div class="detail-section">
        <div class="section-title">状态分析</div>
        <div class="status-info">
          <div>当前阶段：<strong>{{ detail.current_stage || '-' }}</strong></div>
          <div>当前阶段已用：<strong>{{ detail.days_in_stage }}天</strong> / 剩余 <strong>{{ detail.days_remaining }}天</strong></div>
          <div>总已用：<strong>{{ detail.total_days_used }}天</strong> / 总时限 <strong>{{ detail.total_days_limit }}天</strong></div>
          <div v-if="detail.status === 'overdue'">
            超期类型：<strong>{{ overdueTypeLabel(detail.overdue_type) }}</strong>
            <span v-if="detail.overdue_stage">（{{ detail.overdue_stage }}）</span>
          </div>
        </div>
      </div>

      <!-- 情况说明 -->
      <div class="detail-section">
        <div class="section-title">情况说明</div>
        <el-input type="textarea" v-model="remark" :rows="3" placeholder="输入最新进展情况..." />
        <el-button type="primary" size="small" @click="saveRemark" style="margin-top: 8px;">保存情况说明</el-button>
      </div>

      <!-- 阶段时间节点编辑 -->
      <div class="detail-section">
        <div class="section-title">阶段时间节点</div>
        <div class="date-fields">
          <div v-for="field in dateFields" :key="field.key" class="date-field">
            <span class="label">{{ field.label }}</span>
            <el-date-picker v-model="editForm[field.key]" type="date" value-format="YYYY-MM-DD" :placeholder="'选择日期'" size="small" />
          </div>
        </div>
        <el-button type="primary" size="small" @click="saveDates" style="margin-top: 12px;">保存时间节点</el-button>
      </div>
    </div>

    <template #footer>
      <el-button type="danger" @click="deleteProject">删除项目</el-button>
      <el-button @click="$emit('close')">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi } from '../api/projects'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({ projectId: Number })
const emit = defineEmits(['close', 'updated'])

const loading = ref(false)
const detail = ref({})
const remark = ref('')
const editForm = ref({})

const dateFields = [
  { key: 'bid_notice_date', label: '中标通知书获得' },
  { key: 'contract_content_settled_date', label: '合同内容敲定' },
  { key: 'contract_start_date', label: '合同发起' },
  { key: 'contract_approved_date', label: '合同完成审批' },
  { key: 'contract_signed_date', label: '完成签约' },
  { key: 'contract_filed_date', label: '合同归档' },
  { key: 'biz_analysis_date', label: '业务解构完成' },
  { key: 'contract_parse_date', label: '合同解析完成' },
  { key: 'ict_provincial_date', label: '省内ICT立项' },
  { key: 'ict_digital_date', label: '数智ICT立项' },
]

const overdueTypeLabel = (type) => ({
  stage_overdue: '阶段超期', total_overdue: '总时长超期', both: '双重超期', none: '-',
}[type] || type)

async function loadDetail() {
  loading.value = true
  try {
    detail.value = await projectApi.get(props.projectId)
    remark.value = detail.value.status_remark || ''
    dateFields.forEach(f => { editForm.value[f.key] = detail.value[f.key] || null })
    // 基本信息字段
    editForm.value.name = detail.value.name || ''
    editForm.value.region = detail.value.region || ''
    editForm.value.responsible_person = detail.value.responsible_person || ''
    editForm.value.amount = detail.value.amount || null
    editForm.value.bid_subject = detail.value.bid_subject || ''
  } catch (e) {
    ElMessage.error('加载详情失败')
  } finally {
    loading.value = false
  }
}

async function saveRemark() {
  try {
    await projectApi.updateRemark(props.projectId, remark.value)
    ElMessage.success('情况说明已保存')
    emit('updated')
    await loadDetail()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function saveBasic() {
  try {
    await projectApi.update(props.projectId, {
      name: editForm.value.name || null,
      region: editForm.value.region || null,
      responsible_person: editForm.value.responsible_person || null,
      amount: editForm.value.amount ?? null,
      bid_subject: editForm.value.bid_subject || null,
    })
    ElMessage.success('基本信息已保存')
    emit('updated')
    await loadDetail()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function saveDates() {
  try {
    const data = {}
    dateFields.forEach(f => { data[f.key] = editForm.value[f.key] || null })
    await projectApi.update(props.projectId, data)
    ElMessage.success('时间节点已保存')
    emit('updated')
    await loadDetail()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目「${detail.value.name}」吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    await projectApi.delete(props.projectId)
    ElMessage.success('已删除')
    emit('updated')
    emit('close')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.detail-section { margin-bottom: 20px; }
.section-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border-color); }
.info-form { display: flex; flex-direction: column; gap: 10px; }
.form-row { display: flex; align-items: center; gap: 8px; }
.form-row label { min-width: 90px; font-size: 13px; color: var(--text-secondary); flex-shrink: 0; }
.form-row .el-input, .form-row .el-select, .form-row .el-input-number { flex: 1; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; }
.form-grid .form-row { display: flex; align-items: center; gap: 8px; }
.timeline { display: flex; gap: 4px; flex-direction: column; }
.timeline-item { display: flex; align-items: center; gap: 12px; padding: 6px 0; }
.timeline-stage { width: 80px; font-size: 13px; }
.timeline-bar { flex: 1; height: 8px; background: var(--bg-card); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.timeline-item.normal .bar-fill { background: var(--color-normal); }
.timeline-item.warning .bar-fill { background: var(--color-warning); }
.timeline-item.overdue .bar-fill { background: var(--color-overdue); }
.timeline-item.completed .bar-fill { background: var(--color-completed); }
.timeline-item.pending .bar-fill { background: var(--border-color); }
.timeline-info { display: flex; flex-direction: column; font-size: 12px; min-width: 120px; }
.timeline-date { color: var(--text-secondary); }
.status-info div { padding: 4px 0; }
.date-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.date-field { display: flex; align-items: center; gap: 8px; }
.date-field .label { min-width: 100px; font-size: 13px; color: var(--text-secondary); }
</style>
