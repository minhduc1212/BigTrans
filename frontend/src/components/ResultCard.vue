<template>
  <div 
    class="result-card glass-panel"
    :class="{ 
      'loading': result.loading, 
      'error-state': !result.loading && !result.success,
      'success-state': !result.loading && result.success 
    }"
  >
    <div class="card-header">
      <div class="engine-info-wrapper">
        <span class="engine-dot" :class="result.engine_id"></span>
        <h4 class="engine-title">{{ result.engine_name }}</h4>
      </div>
      
      <div class="card-meta">
        <!-- Latency / Cache Badge -->
        <span v-if="!result.loading && result.success" class="latency-badge">
          {{ result.latency_ms === 0 ? 'Cached' : `${result.latency_ms} ms` }}
        </span>
        
        <!-- Copy Button -->
        <button 
          v-if="!result.loading && result.success && result.translated_text"
          class="copy-btn"
          @click="copyText"
          :title="'Copy ' + result.engine_name + ' translation'"
        >
          <CheckIcon v-if="copied" class="copied-icon" />
          <CopyIcon v-else class="copy-icon" />
        </button>
      </div>
    </div>
    
    <div class="card-body">
      <!-- Loading State -->
      <div v-if="result.loading" class="skeleton-loader">
        <div class="skeleton-line"></div>
        <div class="skeleton-line width-70"></div>
        <div class="skeleton-line width-85"></div>
      </div>
      
      <!-- Error State -->
      <div v-else-if="!result.success" class="error-container">
        <AlertTriangleIcon class="error-icon" />
        <p class="error-msg">{{ result.error_message || 'Translation failed' }}</p>
      </div>
      
      <!-- Text Result -->
      <p v-else class="translation-text">
        {{ result.translated_text }}
      </p>
    </div>

    <!-- Inline Copy Toast Alert -->
    <transition name="fade">
      <div v-if="copied" class="copy-toast">
        Copied to clipboard!
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { 
  Copy as CopyIcon, 
  Check as CheckIcon, 
  AlertTriangle as AlertTriangleIcon 
} from 'lucide-vue-next';

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
});

const copied = ref(false);

async function copyText() {
  if (!props.result.translated_text) return;
  try {
    await navigator.clipboard.writeText(props.result.translated_text);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy translation:', err);
  }
}
</script>

<style scoped>
.result-card {
  position: relative;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 140px;
  overflow: hidden;
}

.result-card.loading {
  border-color: rgba(255, 255, 255, 0.05);
}

.result-card.success-state {
  border-color: var(--border-color-active);
}

.result-card.error-state {
  border-color: rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.02);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  padding-bottom: 0.5rem;
}

.engine-info-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.engine-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.engine-dot.google { background: var(--accent-cyan); }
.engine-dot.bing { background: var(--accent-purple); }
.engine-dot.baidu { background: var(--warning); }
.engine-dot.deepl { background: var(--success); }
.engine-dot.default { background: var(--text-muted); }

.engine-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.latency-badge {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.04);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  border-color: rgba(255, 255, 255, 0.15);
}

.copy-icon, .copied-icon {
  width: 14px;
  height: 14px;
}

.copied-icon {
  color: var(--success);
}

.card-body {
  flex-grow: 1;
}

.translation-text {
  font-size: 1.025rem;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
}

/* Skeleton Loading Animation */
.skeleton-loader {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.skeleton-line {
  height: 16px;
  background: var(--skeleton-bg);
  background-size: 200% 100%;
  animation: loading-pulse 1.5s infinite;
  border-radius: 4px;
  width: 100%;
}

.width-70 { width: 70%; }
.width-85 { width: 85%; }

@keyframes loading-pulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Error State Styles */
.error-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--danger);
  padding: 0.5rem 0;
}

.error-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.error-msg {
  font-size: 0.875rem;
  line-height: 1.4;
}

/* Inline Toast styling */
.copy-toast {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  background: rgba(16, 185, 129, 0.95);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  box-shadow: var(--shadow-md);
  z-index: 10;
  backdrop-filter: blur(4px);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
