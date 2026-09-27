<template>
  <div class="board-view" v-loading="loading">
    <div class="board-columns">
      <div v-for="stage in stages" :key="stage.name" class="board-column">
        <div class="column-header">
          <span>{{ stage.name }}</span>
          <span class="column-count">{{ stageProjects(stage.name).length }}</span>
        </div>
        <div class="column-body">
          <div
            v-for="item in stageProjects(stage.name)"
            :key="item.id"
            class="project-card"
            :class="item.status"
            @click="openDetail(item.id)"
          >
            <div class="card-name">{{ item.name }}</div>
            <div class="card-info">
              <span>{{ item.region || '-' }}</span>
              <span>{{ item.amount ? item.amount + '万' : '-' }}</span>
            </div>
            <div class="card-days">
              <span v-if="item.days_in_stage > 0">{{ item.days_in_stage }}/{{ item.total_days_limit }}天</span>
              <span v-else-if="item.status === 'completed'">已完成</span>
              <span v-else>待开始</span>
            </div>
          </div>
          <div v-if="stageProjects(stage.name).length === 0" class="empty-column">暂无项目</div>
        </div>
      </div>
    </div>

    <ProjectDetail v-if="detailVisible" :project-id="detailId" @close="detailVisible = false" @updated="loadData" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectApi } from '../api/projects'
import ProjectDetail from '../components/ProjectDetail.vue'

const loading = ref(false)
const projects = ref([])
const stages = ref([
  { name: '合同敲定' }, { name: '合同审批' }, { name: '业务解构' },
  { name: '合同解析' }, { name: 'ICT立项' },
])
const detailVisible = ref(false)
const detailId = ref(null)

function stageProjects(stageName) {
  return projects.value.filter(p => p.current_stage === stageName)
}

function openDetail(id) {
  detailId.value = id
  detailVisible.value = true
}

async function loadData() {
  loading.value = true
  try {
    const res = await projectApi.list({ page: 1, size: 200 })
    projects.value = res.items
  } catch (e) {
    console.error('加载项目失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.board-columns { display: flex; gap: 12px; overflow-x: auto; min-height: calc(100vh - 120px); }
.board-column { flex: 1; min-width: 240px; background: var(--bg-secondary); border-radius: 10px; border: 1px solid var(--border-color); display: flex; flex-direction: column; }
.column-header { padding: 12px 16px; font-weight: 600; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); }
.column-count { background: var(--bg-card); padding: 2px 10px; border-radius: 10px; font-size: 12px; color: var(--text-secondary); }
.column-body { flex: 1; padding: 8px; overflow-y: auto; }
.project-card { background: var(--bg-card); border-radius: 8px; padding: 12px; margin-bottom: 8px; cursor: pointer; border-left: 3px solid var(--border-color); transition: transform 0.1s; }
.project-card:hover { transform: translateX(2px); }
.project-card.normal { border-left-color: var(--color-normal); }
.project-card.warning { border-left-color: var(--color-warning); }
.project-card.overdue { border-left-color: var(--color-overdue); }
.project-card.completed { border-left-color: var(--color-completed); }
.card-name { font-size: 14px; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-info { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); }
.card-days { font-size: 12px; margin-top: 4px; color: var(--text-secondary); }
.empty-column { text-align: center; color: var(--text-secondary); padding: 20px 0; font-size: 13px; }
</style>
