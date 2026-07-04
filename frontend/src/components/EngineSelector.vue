<template>
  <div class="engine-selector glass-panel">
    <div class="selector-header">
      <CpuIcon class="header-icon" />
      <h3>Translation Engines</h3>
    </div>
    
    <div class="engines-grid">
      <div 
        v-for="engine in store.engines" 
        :key="engine.id"
        class="engine-card"
        :class="{ 
          'active': store.selectedEngines.includes(engine.id),
          'disabled': !engine.available
        }"
        @click="engine.available && store.toggleEngine(engine.id)"
      >
        <div class="engine-card-header">
          <span class="checkbox-wrapper">
            <span class="custom-checkbox">
              <CheckIcon v-if="store.selectedEngines.includes(engine.id)" class="check-icon" />
            </span>
          </span>
          <span class="engine-name">{{ engine.name }}</span>
        </div>
        
        <p class="engine-desc">{{ getEngineDesc(engine.id) }}</p>
        
        <div class="tags-row">
          <span class="badge" :class="getBadgeClass(engine.id)">
            {{ getEngineTag(engine.id) }}
          </span>
        </div>
        
        <!-- Status tooltip if disabled -->
        <div v-if="!engine.available" class="disabled-overlay">
          <span class="disabled-tooltip">Engine temporarily unavailable</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { store } from '../store';
import { Cpu as CpuIcon, Check as CheckIcon } from 'lucide-vue-next';

function getEngineDesc(id) {
  const descriptions = {
    google: 'Global leader in translations. High stability, fast latency.',
    google_pip: 'Google Translate wrapper powered by the deep-translator library.',
    bing: 'Microsoft Translate. Highly recommended for Asian literature.',
    deepl: 'Superb sentence flow and natural grammar. Fluent output.',
    baidu: 'Excellent for Chinese-Vietnamese novels, slang & cultivation terms.',
    sogou: 'Popular Chinese search engine translator. Excellent colloquial flow.',
    youdao: 'NetEase translation engine. Very familiar with fantasy novel terms.'
  };
  return descriptions[id] || 'Third-party translation engine adapter.';
}

function getEngineTag(id) {
  const tags = {
    google: 'Fast & Stable',
    google_pip: 'Stable (Lib)',
    bing: 'Best for Novels',
    deepl: 'Ultra Fluent',
    baidu: 'Cultivation Expert',
    sogou: 'Novel Expert (Lib)',
    youdao: 'Cultivation (Lib)'
  };
  return tags[id] || 'General';
}

function getBadgeClass(id) {
  const classes = {
    google: 'badge-google',
    google_pip: 'badge-google',
    bing: 'badge-bing',
    deepl: 'badge-deepl',
    baidu: 'badge-baidu',
    sogou: 'badge-baidu',
    youdao: 'badge-bing'
  };
  return classes[id] || 'badge-default';
}
</script>

<style scoped>
.engine-selector {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.header-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: var(--primary);
}

.selector-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  color: var(--text-primary);
}

.engines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.engine-card {
  position: relative;
  background: var(--bg-subcard);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.2rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 0.8rem;
  transition: all var(--transition-normal);
  user-select: none;
}

.engine-card:hover:not(.disabled) {
  transform: translateY(-2px);
  border-color: var(--border-color-active);
  background: var(--bg-card-hover);
}

.engine-card.active {
  border-color: var(--primary);
  background: var(--primary-light);
  box-shadow: var(--shadow-sm);
}

.engine-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.checkbox-wrapper {
  display: inline-flex;
}

.custom-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 1.5px solid var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.engine-card.active .custom-checkbox {
  background: var(--primary);
  border-color: var(--primary);
}

.check-icon {
  width: 12px;
  height: 12px;
  color: var(--bg-main);
  stroke-width: 3;
}

.engine-name {
  font-weight: 600;
  font-size: 1.05rem;
  color: var(--text-primary);
}

.engine-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.4;
  flex-grow: 1;
}

.tags-row {
  display: flex;
  gap: 0.5rem;
}

.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
}

.badge-google {
  background: rgba(6, 182, 212, 0.12);
  color: var(--accent-cyan);
}

.badge-bing {
  background: rgba(168, 85, 247, 0.12);
  color: var(--accent-purple);
}

.badge-baidu {
  background: rgba(245, 158, 11, 0.12);
  color: var(--warning);
}

.badge-deepl {
  background: rgba(16, 185, 129, 0.12);
  color: var(--success);
}

.badge-default {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
}

/* Disabled state */
.engine-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: var(--danger);
}

.disabled-overlay {
  position: absolute;
  inset: 0;
  background: rgba(11, 15, 25, 0.6);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
}

.disabled-tooltip {
  background: var(--danger);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 4px;
  box-shadow: var(--shadow-md);
}
</style>
