<template>
  <div class="app-layout">
    <!-- Header -->
    <header class="app-header">
      <div class="header-main-row">
        <div class="logo-wrapper">
          <LanguagesIcon class="logo-icon" />
          <h1 class="app-title">Gibsnart</h1>
        </div>
        
        <!-- Theme Toggle Button -->
        <button class="theme-toggle-btn" @click="store.toggleTheme" :title="store.theme === 'theme-dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
          <SunIcon v-if="store.theme === 'theme-dark'" class="theme-icon" />
          <MoonIcon v-else class="theme-icon" />
        </button>
      </div>
      <p class="app-subtitle">Multi-Engine Parallel Translator for Web Novel Translators & Readers</p>
    </header>

    <main class="main-content">
      <!-- Left Controls Panel -->
      <div class="controls-panel">
        <LanguagePicker />
        <TextInput />
        <EngineSelector />
        
        <!-- Translation History -->
        <div v-if="store.history.length > 0" class="history-panel glass-panel">
          <div class="history-header">
            <HistoryIcon class="history-icon-small" />
            <h4>Recent Translations</h4>
            <button class="clear-history-btn" @click="store.clearHistory" title="Clear all history">
              Clear All
            </button>
          </div>
          <ul class="history-list">
            <li 
              v-for="(item, idx) in store.history" 
              :key="idx"
              class="history-item"
              @click="loadHistoryItem(item)"
            >
              <span class="history-text">{{ item.text }}</span>
              <span class="history-langs">
                {{ item.source }} <ArrowRightIcon class="lang-arrow" /> {{ item.target }}
              </span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Right Results Panel -->
      <div class="results-panel">
        <!-- Results Header Controls -->
        <div class="results-header" v-if="hasResults">
          <h3>Translations</h3>
          <button 
            v-if="hasSuccessfulResults"
            class="copy-all-btn" 
            @click="copyAllTranslations"
          >
            <CheckIcon v-if="allCopied" class="btn-icon" />
            <CopyIcon v-else class="btn-icon" />
            {{ allCopied ? 'All Copied!' : 'Copy All Results' }}
          </button>
        </div>

        <!-- Grid of results -->
        <div v-if="hasActiveTranslations" class="results-grid">
          <ResultCard 
            v-for="(res, engineId) in store.translations" 
            :key="engineId"
            :result="res"
          />
        </div>

        <!-- Empty State / Welcome Screen -->
        <div v-else class="welcome-screen glass-panel">
          <h2>Select translation engines and type text to begin</h2>
          <p>Gibsnart executes parallel queries to compare quality across Google, Bing, Baidu, and DeepL.</p>
          
          <div class="quick-examples">
            <h4>Try Novel Examples (Chinese):</h4>
            <div class="examples-grid">
              <button 
                v-for="(ex, i) in novelExamples" 
                :key="i"
                class="example-btn"
                @click="loadExample(ex)"
              >
                "{{ ex.text }}"
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="app-footer">
      <p>&copy; 2026 Gibsnart Translator. All rights reserved. Powered by FastAPI & Vue.js.</p>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue';
import { store } from './store';
import LanguagePicker from './components/LanguagePicker.vue';
import TextInput from './components/TextInput.vue';
import EngineSelector from './components/EngineSelector.vue';
import ResultCard from './components/ResultCard.vue';

import { 
  Languages as LanguagesIcon, 
  History as HistoryIcon,
  ArrowRight as ArrowRightIcon,
  Copy as CopyIcon,
  Check as CheckIcon,
  Sun as SunIcon,
  Moon as MoonIcon
} from 'lucide-vue-next';

onMounted(() => {
  store.fetchEngines();
  document.body.className = store.theme;
});

const novelExamples = [
  { text: '我加载了神秘学面板', source: 'zh', target: 'vi' },
  { text: '那一处处坍塌的屋舍，一具具青黑色的尸体', source: 'zh', target: 'vi' },
  { text: 'The protagonist suddenly transmigrated into a cultivation world.', source: 'en', target: 'vi' }
];

const hasActiveTranslations = computed(() => {
  return Object.keys(store.translations).length > 0;
});

const hasResults = computed(() => {
  return Object.keys(store.translations).length > 0;
});

const hasSuccessfulResults = computed(() => {
  return Object.values(store.translations).some(res => !res.loading && res.success && res.translated_text);
});

const allCopied = ref(false);

function loadExample(example) {
  store.inputText = example.text;
  store.setLanguages(example.source, example.target);
  store.translate();
}

function loadHistoryItem(item) {
  store.inputText = item.text;
  store.setLanguages(item.source, item.target);
  store.translate();
}

async function copyAllTranslations() {
  const successfulTranslations = Object.values(store.translations)
    .filter(res => !res.loading && res.success && res.translated_text);
    
  if (successfulTranslations.length === 0) return;
  
  // Format as:
  // [Google Translate]: translated text...
  // [Baidu Translate]: translated text...
  const formattedText = successfulTranslations
    .map(res => `[${res.engine_name}]: ${res.translated_text}`)
    .join('\n\n');
    
  try {
    await navigator.clipboard.writeText(formattedText);
    allCopied.value = true;
    setTimeout(() => {
      allCopied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy all results:', err);
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  gap: 2rem;
}

.app-header {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.header-main-row {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  position: relative;
}

.theme-toggle-btn {
  position: absolute;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
}

.theme-toggle-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary);
  color: var(--primary);
  transform: scale(1.05);
}

.theme-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.logo-icon {
  width: 2.5rem;
  height: 2.5rem;
  color: var(--primary);
}

.app-title {
  font-size: 2.8rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--primary);
}

.app-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  font-weight: 400;
}

.main-content {
  display: grid;
  grid-template-columns: 450px 1fr;
  gap: 2rem;
  align-items: start;
}

@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}

.controls-panel {
  display: flex;
  flex-direction: column;
}

/* History styling */
.history-panel {
  padding: 1.25rem;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  padding-bottom: 0.5rem;
}

.history-icon-small {
  width: 1rem;
  height: 1rem;
  color: var(--text-muted);
}

.history-header h4 {
  font-size: 0.95rem;
  font-weight: 600;
  flex-grow: 1;
  color: var(--text-primary);
}

.clear-history-btn {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--danger);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.clear-history-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

.history-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0.75rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
}

.history-text {
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 250px;
  color: var(--text-primary);
}

.history-langs {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.25rem;
  white-space: nowrap;
}

.lang-arrow {
  width: 10px;
  height: 10px;
}

/* Results panel styling */
.results-panel {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-height: 400px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-header h3 {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.copy-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--primary-light);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
}

.copy-all-btn:hover {
  background: var(--primary);
  color: var(--bg-main);
  border-color: var(--primary);
}

.results-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}

@media (min-width: 1200px) {
  .results-grid {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  }
}

/* Welcome Screen */
.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 2rem;
  flex-grow: 1;
  gap: 1rem;
}

.welcome-icon {
  width: 3.5rem;
  height: 3.5rem;
  color: var(--primary);
  filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.3));
  margin-bottom: 0.5rem;
}

.welcome-screen h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.welcome-screen p {
  color: var(--text-secondary);
  max-width: 480px;
  font-size: 0.95rem;
  line-height: 1.6;
}

.quick-examples {
  margin-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  padding-top: 1.5rem;
  width: 100%;
  max-width: 500px;
}

.quick-examples h4 {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.examples-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.example-btn {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 0.875rem;
  padding: 0.6rem 1rem;
  border-radius: var(--radius-sm);
  text-align: left;
  transition: all var(--transition-fast);
}

.example-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.15);
}

.app-footer {
  text-align: center;
  padding: 2rem 0;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
  font-size: 0.85rem;
}
</style>
