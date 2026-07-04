<template>
  <div class="language-picker glass-panel">
    <div class="picker-group">
      <label for="source-lang">From</label>
      <select 
        id="source-lang" 
        v-model="sourceModel" 
        @change="updateLanguages"
      >
        <option value="auto">Auto Detect</option>
        <option v-for="lang in languages" :key="'src-' + lang.code" :value="lang.code">
          {{ lang.name }}
        </option>
      </select>
    </div>

    <button 
      class="swap-btn" 
      @click="swapLanguages" 
      title="Swap languages"
      :disabled="store.sourceLang === 'auto'"
    >
      <ArrowLeftRightIcon class="swap-icon" />
    </button>

    <div class="picker-group">
      <label for="target-lang">To</label>
      <select 
        id="target-lang" 
        v-model="targetModel" 
        @change="updateLanguages"
      >
        <option v-for="lang in targetLanguages" :key="'tgt-' + lang.code" :value="lang.code">
          {{ lang.name }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { store } from '../store';
import { ArrowRightLeft as ArrowLeftRightIcon } from 'lucide-vue-next';

const languages = [
  { code: 'zh', name: 'Chinese' },
  { code: 'vi', name: 'Vietnamese' },
  { code: 'en', name: 'English' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'ru', name: 'Russian' }
];

// Target languages cannot be 'auto'
const targetLanguages = computed(() => {
  return languages.filter(l => l.code !== store.sourceLang);
});

const sourceModel = computed({
  get: () => store.sourceLang,
  set: (val) => {
    if (val === store.targetLang) {
      // If user sets source to match target, change target to something else
      const defaultTarget = val === 'vi' ? 'zh' : 'vi';
      store.setLanguages(val, defaultTarget);
    } else {
      store.setLanguages(val, store.targetLang);
    }
  }
});

const targetModel = computed({
  get: () => store.targetLang,
  set: (val) => {
    store.setLanguages(store.sourceLang, val);
  }
});

function swapLanguages() {
  if (store.sourceLang === 'auto') return;
  const oldSrc = store.sourceLang;
  const oldTgt = store.targetLang;
  store.setLanguages(oldTgt, oldSrc);
  if (store.inputText) {
    store.translate();
  }
}

function updateLanguages() {
  if (store.inputText) {
    store.translate();
  }
}
</script>

<style scoped>
.language-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
}

.picker-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.picker-group label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}

select {
  width: 100%;
  padding: 0.6rem 1rem;
  font-size: 0.95rem;
  font-weight: 500;
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  cursor: pointer;
}

.swap-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--bg-subcard);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  margin-top: 1.2rem;
  transition: all var(--transition-fast);
}

.swap-btn:hover:not(:disabled) {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--bg-main);
  transform: rotate(180deg);
  box-shadow: var(--shadow-sm);
}

.swap-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.swap-icon {
  width: 1.1rem;
  height: 1.1rem;
}
</style>
