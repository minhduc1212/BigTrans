<template>
  <div class="text-input-container glass-panel">
    <div class="input-actions-top">
      <span class="char-count" :class="{ 'warning': store.inputText.length > 4000 }">
        {{ store.inputText.length }} / 5000 characters
      </span>
      
      <!-- Stream mode toggle -->
      <div class="toggle-container" title="Use streaming (results load as they finish)">
        <span class="toggle-label">Stream mode</span>
        <label class="switch">
          <input type="checkbox" v-model="store.streamMode">
          <span class="slider"></span>
        </label>
      </div>
    </div>
    
    <div class="textarea-wrapper">
      <textarea
        v-model="store.inputText"
        placeholder="Type or paste text here to translate..."
        maxlength="5000"
        @keydown.enter.ctrl.prevent="triggerTranslate"
        rows="6"
      ></textarea>
      
      <button 
        v-if="store.inputText" 
        class="clear-btn" 
        @click="clearText" 
        title="Clear text"
      >
        <XIcon class="clear-icon" />
      </button>
    </div>
    
    <div class="actions-row">
      <button class="action-btn secondary-btn" @click="pasteFromClipboard" title="Paste from clipboard">
        <ClipboardIcon class="btn-icon" />
        Paste
      </button>
      
      <button 
        class="action-btn primary-btn" 
        :disabled="!store.inputText.trim() || store.isTranslating" 
        @click="triggerTranslate"
      >
        <span v-if="store.isTranslating" class="spinner"></span>
        <TranslateIcon v-else class="btn-icon" />
        {{ store.isTranslating ? 'Translating...' : 'Translate (Ctrl+Enter)' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { store } from '../store';
import { 
  Clipboard as ClipboardIcon, 
  Languages as TranslateIcon, 
  X as XIcon 
} from 'lucide-vue-next';

function clearText() {
  store.inputText = '';
}

async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    store.inputText = text;
  } catch (err) {
    console.error('Failed to read clipboard:', err);
  }
}

function triggerTranslate() {
  store.translate();
}
</script>

<style scoped>
.text-input-container {
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.input-actions-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.char-count {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.char-count.warning {
  color: var(--warning);
}

.toggle-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  user-select: none;
}

.toggle-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Switch Styles */
.switch {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--border-color);
  border-radius: 34px;
  transition: .3s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 12px;
  width: 12px;
  left: 3px;
  bottom: 3px;
  background-color: var(--text-secondary);
  border-radius: 50%;
  transition: .3s;
}

input:checked + .slider {
  background-color: var(--primary-light);
  border-color: var(--primary);
}

input:checked + .slider:before {
  transform: translateX(16px);
  background-color: var(--primary);
}

.textarea-wrapper {
  position: relative;
  margin-bottom: 1rem;
}

textarea {
  width: 100%;
  padding: 1rem 2.5rem 1rem 1rem;
  font-size: 1.05rem;
  line-height: 1.6;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-input);
  resize: vertical;
}

.clear-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: var(--text-primary);
}

.clear-icon {
  width: 14px;
  height: 14px;
}

.actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  font-size: 0.95rem;
  border-radius: var(--radius-md);
}

.secondary-btn {
  background: var(--bg-subcard);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.secondary-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-color-active);
}

.primary-btn {
  background: var(--primary);
  color: var(--bg-main);
  box-shadow: var(--shadow-sm);
}

.primary-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  box-shadow: var(--shadow-md);
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-icon {
  width: 1.1rem;
  height: 1.1rem;
}

/* Spinner */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
