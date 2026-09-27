<template>
  <div class="metric-card" :class="type">
    <div class="metric-value">{{ value }}</div>
    <div class="metric-label">{{ label }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [Number, String],
  type: { type: String, default: 'default' },
})
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
