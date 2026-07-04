import { reactive, ref, watch } from 'vue';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const store = reactive({
  // State
  engines: [],
  selectedEngines: JSON.parse(localStorage.getItem('gibsnart_selected_engines')) || ['google', 'bing'],
  sourceLang: localStorage.getItem('gibsnart_source_lang') || 'auto',
  targetLang: localStorage.getItem('gibsnart_target_lang') || 'vi',
  inputText: '',
  translations: {},
  history: JSON.parse(localStorage.getItem('gibsnart_history')) || [],
  isTranslating: false,
  streamMode: true,
  theme: localStorage.getItem('gibsnart_theme') || 'theme-dark',

  // Actions
  toggleTheme() {
    this.theme = this.theme === 'theme-dark' ? 'theme-light' : 'theme-dark';
    localStorage.setItem('gibsnart_theme', this.theme);
    document.body.className = this.theme;
  },
  async fetchEngines() {
    try {
      const response = await fetch(`${API_BASE_URL}/engines`);
      if (!response.ok) throw new Error('Failed to fetch engines');
      const data = await response.json();
      this.engines = data;
      
      // Filter out any selected engines that are no longer available
      const availableIds = data.map(e => e.id);
      this.selectedEngines = this.selectedEngines.filter(id => availableIds.includes(id));
      if (this.selectedEngines.length === 0 && availableIds.length > 0) {
        this.selectedEngines = [availableIds[0]];
      }
    } catch (error) {
      console.error('Error fetching engines:', error);
    }
  },

  toggleEngine(engineId) {
    const index = this.selectedEngines.indexOf(engineId);
    if (index > -1) {
      if (this.selectedEngines.length > 1) {
        this.selectedEngines.splice(index, 1);
      }
    } else {
      this.selectedEngines.push(engineId);
    }
    localStorage.setItem('gibsnart_selected_engines', JSON.stringify(this.selectedEngines));
  },

  setLanguages(source, target) {
    this.sourceLang = source;
    this.targetLang = target;
    localStorage.setItem('gibsnart_source_lang', source);
    localStorage.setItem('gibsnart_target_lang', target);
  },

  addToHistory(text, source, target) {
    if (!text.trim()) return;
    // Remove if already exists to move it to top
    this.history = this.history.filter(item => item.text !== text);
    this.history.unshift({ text, source, target, timestamp: Date.now() });
    // Cap at 10 items
    if (this.history.length > 10) {
      this.history.pop();
    }
    localStorage.setItem('gibsnart_history', JSON.stringify(this.history));
  },

  clearHistory() {
    this.history = [];
    localStorage.removeItem('gibsnart_history');
  },

  async translate() {
    const text = this.inputText.trim();
    if (!text || this.selectedEngines.length === 0) return;

    this.isTranslating = true;
    this.addToHistory(text, this.sourceLang, this.targetLang);

    // Initialize translations dictionary for active engines
    this.translations = {};
    for (const engineId of this.selectedEngines) {
      const engine = this.engines.find(e => e.id === engineId);
      this.translations[engineId] = {
        engine_id: engineId,
        engine_name: engine ? engine.name : engineId,
        loading: true,
        success: false,
        translated_text: '',
        latency_ms: 0,
        error_message: null
      };
    }

    // Determine if we should use streaming (SSE) or fallback to POST
    // Fallback to POST if text is longer than 1500 chars to avoid URL length issues
    if (this.streamMode && text.length <= 1500) {
      this.translateStream(text);
    } else {
      await this.translatePost(text);
    }
  },

  translateStream(text) {
    const params = new URLSearchParams({
      text: text,
      source: this.sourceLang,
      target: this.targetLang,
      engines: this.selectedEngines.join(',')
    });

    const url = `${API_BASE_URL}/translate/stream?${params.toString()}`;
    const eventSource = new EventSource(url);
    
    let receivedCount = 0;
    const expectedCount = this.selectedEngines.length;

    eventSource.onmessage = (event) => {
      try {
        const result = JSON.parse(event.data);
        const engineId = result.engine_id;
        
        if (this.translations[engineId]) {
          this.translations[engineId] = {
            ...this.translations[engineId],
            loading: false,
            success: result.success,
            translated_text: result.translated_text || '',
            latency_ms: result.latency_ms,
            error_message: result.error_message
          };
        }
        
        receivedCount++;
        if (receivedCount >= expectedCount) {
          eventSource.close();
          this.isTranslating = false;
        }
      } catch (err) {
        console.error('Error parsing SSE message:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      eventSource.close();
      
      // Any engine still loading has failed
      for (const engineId of this.selectedEngines) {
        if (this.translations[engineId] && this.translations[engineId].loading) {
          this.translations[engineId].loading = false;
          this.translations[engineId].success = false;
          this.translations[engineId].error_message = 'Connection closed or timeout';
        }
      }
      this.isTranslating = false;
    };
  },

  async translatePost(text) {
    try {
      const response = await fetch(`${API_BASE_URL}/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: text,
          source_lang: this.sourceLang,
          target_lang: this.targetLang,
          engines: this.selectedEngines
        })
      });

      if (!response.ok) throw new Error('API Request Failed');
      
      const data = await response.json();
      
      for (const result of data.results) {
        const engineId = result.engine_id;
        if (this.translations[engineId]) {
          this.translations[engineId] = {
            ...this.translations[engineId],
            loading: false,
            success: result.success,
            translated_text: result.translated_text || '',
            latency_ms: result.latency_ms,
            error_message: result.error_message
          };
        }
      }
    } catch (error) {
      console.error('POST translate failed:', error);
      // Mark all loading ones as failed
      for (const engineId of this.selectedEngines) {
        if (this.translations[engineId]) {
          this.translations[engineId].loading = false;
          this.translations[engineId].success = false;
          this.translations[engineId].error_message = error.message || 'Translation failed';
        }
      }
    } finally {
      this.isTranslating = false;
    }
  }
});
