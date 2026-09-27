<template>
  <span class="status-badge" :class="status">
    <span class="dot"></span>
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'normal' },
})

const labelMap = {
  normal: '正常',
  warning: '预警',
  overdue: '超期',
  completed: '已完成',
}

const label = computed(() => labelMap[props.status] || props.status)
</script>

<style scoped>
.dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
</style>
