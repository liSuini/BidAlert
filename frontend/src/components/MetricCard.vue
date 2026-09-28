<template>
  <div class="metric-card" :class="type" :style="{ cursor: clickable ? 'pointer' : 'default' }" @click="onClick">
    <div class="metric-value">{{ value }}</div>
    <div class="metric-label">{{ label }}</div>
  </div>
</template>

<script setup>
const props = defineProps({
  label: String,
  value: [Number, String],
  type: { type: String, default: 'default' },
  clickable: { type: Boolean, default: false },
})
const emit = defineEmits(['click'])

function onClick() {
  if (props.clickable) emit('click')
}
</script>

<style scoped>
.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 20px 24px;
  text-align: center;
  min-width: 140px;
  flex: 1;
  transition: transform 0.15s, border-color 0.15s;
}
.metric-card[style*="pointer"]:hover {
  transform: translateY(-2px);
  border-color: var(--text-secondary);
}
.metric-card .metric-value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 4px;
}
.metric-card .metric-label {
  font-size: 14px;
  color: var(--text-secondary);
}
.metric-card.default .metric-value { color: var(--text-primary); }
.metric-card.normal .metric-value { color: var(--color-normal); }
.metric-card.warning .metric-value { color: var(--color-warning); }
.metric-card.overdue .metric-value { color: var(--color-overdue); }
.metric-card.completed .metric-value { color: var(--color-completed); }
</style>
