<script setup>
import { ref } from 'vue';
import { 
  Search, 
  Link, 
  Mail, 
  Play, 
  Loader2, 
  Sparkles, 
  Settings, 
  Server, 
  Cloud 
} from 'lucide-vue-next';

// --- State Management ---
const mode = ref('topic');
const topic = ref('');
const urlInput = ref(''); 
const email = ref('');
const output = ref('');
const loading = ref(false);
const error = ref('');

// --- Settings State ---
const showSettings = ref(false);
const useLocalBackend = ref(true); // Default to local
const backendUrl = ref('http://192.168.1.160:8000/learning_summary');
const apiKey = ref('');

// --- Main Logic ---
const runSummary = async () => {
  // 1. Validation
  if (mode.value === 'topic' && !topic.value) {
    error.value = 'Please enter a topic.';
    return;
  }
  if (mode.value === 'url' && !urlInput.value) {
    error.value = 'Please enter a URL.';
    return;
  }

  // 2. Reset UI State
  loading.value = true;
  output.value = '';
  error.value = '';

  try {
    let resultText = "";

    if (useLocalBackend.value) {
      // --- LOCAL BACKEND MODE ---
      const response = await fetch(backendUrl.value, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: mode.value,
          topic: topic.value,
          url: urlInput.value,
          email: email.value
        }),
      });

      if (!response.ok) throw new Error(`Server Error: ${response.status}`);
      const data = await response.json();
      resultText = data.summary || "No summary returned from local server.";

    } else {
      // --- CLOUD MODE (Gemini) ---
       const promptText = mode.value === 'topic'
         ? `Provide a comprehensive learning summary for the topic: "${topic.value}". Include key concepts, resources, and a structured learning path.`
         : `Summarize the key learning points from this website/resource: ${urlInput.value}. Focus on educational takeaways.`;
      
       const response = await fetch(
         `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey.value}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ parts: [{ text: promptText }] }],
            tools: [{ google_search: {} }]
          }),
        }
      );

      if (!response.ok) throw new Error(`Gemini API Error: ${response.status}`);
      const data = await response.json();
      resultText = data.candidates?.[0]?.content?.parts?.[0]?.text || "No summary returned.";
    }

    output.value = resultText;

  } catch (err) {
    let msg = err.message;
    if (useLocalBackend.value && msg.includes('Failed to fetch')) {
      msg += " (Check if your local server is running and accessible via CORS)";
    }
    error.value = "Network Error: " + msg;
  } finally {
    loading.value = false;
  }
};

const copyText = () => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(output.value);
  } else {
    const textarea = document.createElement('textarea');
    textarea.value = output.value;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
};
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center p-4 sm:p-8 bg-slate-950 text-slate-100 selection:bg-purple-500 selection:text-white overflow-hidden relative">
    
    <!-- Background Gradient Orbs -->
    <div class="fixed top-20 left-20 w-72 h-72 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
    <div class="fixed top-20 right-20 w-72 h-72 bg-cyan-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

    <div class="relative z-10 w-full max-w-2xl flex flex-col items-center">
      
      <!-- Header -->
      <div class="mb-10 text-center w-full relative">
          <button 
              @click="showSettings = !showSettings"
              class="absolute right-0 top-0 p-2 text-slate-500 hover:text-cyan-400 transition-colors"
              title="Settings"
          >
              <Settings class="w-6 h-6" />
          </button>
        <div class="flex items-center justify-center space-x-3 mb-2">
          <Sparkles class="w-8 h-8 text-cyan-400" />
          <h1 class="text-4xl md:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-cyan-400">
            Research Agent
          </h1>
        </div>
        <p class="text-slate-400 text-lg">Distill knowledge from the web instantly</p>
      </div>

      <!-- Main Card -->
      <div class="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 md:p-8 w-full shadow-2xl transition-all duration-300">
        
        <!-- Settings Panel -->
        <transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 -translate-y-2"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 -translate-y-2"
        >
          <div v-if="showSettings" class="mb-8 p-4 bg-slate-950/50 rounded-xl border border-slate-700">
              <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Connection Settings</h3>
              
              <div class="flex flex-col space-y-4">
                  <div class="flex items-center justify-between bg-slate-900 p-3 rounded-lg border border-slate-800">
                      <span class="text-sm text-slate-300 flex items-center gap-2">
                          <Server v-if="useLocalBackend" class="w-4 h-4 text-emerald-400"/>
                          <Cloud v-else class="w-4 h-4 text-cyan-400"/>
                          Backend Source
                      </span>
                      <button 
                          @click="useLocalBackend = !useLocalBackend"
                          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
                          :class="useLocalBackend ? 'bg-emerald-500' : 'bg-cyan-500'"
                      >
                          <span 
                            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                            :class="useLocalBackend ? 'translate-x-6' : 'translate-x-1'"
                          ></span>
                      </button>
                  </div>

                   <div v-if="useLocalBackend">
                       <label class="text-xs text-slate-500 mb-1 block">Local Server URL</label>
                       <input
                           type="text"
                           v-model="backendUrl"
                           class="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-300 focus:outline-none focus:border-emerald-500"
                       />
                   </div>

                   <div v-if="!useLocalBackend">
                       <label class="text-xs text-slate-500 mb-1 block">Gemini API Key</label>
                       <input
                           type="password"
                           v-model="apiKey"
                           placeholder="Enter your Gemini API key"
                           class="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
                       />
                   </div>
              </div>
          </div>
        </transition>

        <!-- Mode Selection -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-slate-400 mb-2 uppercase tracking-wider">Mode</label>
          <div class="grid grid-cols-2 gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              @click="mode = 'topic'"
              class="flex items-center justify-center space-x-2 py-2.5 rounded-md transition-all duration-200 font-medium"
              :class="mode === 'topic' ? 'bg-slate-800 text-cyan-400 shadow-sm' : 'text-slate-500 hover:text-slate-300'"
            >
              <Search class="w-4 h-4" />
              <span>Search Topic</span>
            </button>
            <button
              @click="mode = 'url'"
              class="flex items-center justify-center space-x-2 py-2.5 rounded-md transition-all duration-200 font-medium"
              :class="mode === 'url' ? 'bg-slate-800 text-purple-400 shadow-sm' : 'text-slate-500 hover:text-slate-300'"
            >
              <Link class="w-4 h-4" />
              <span>Scrape URL</span>
            </button>
          </div>
        </div>

        <!-- Input Fields -->
        <div class="space-y-4 mb-6">
          <div class="relative group">
            <template v-if="mode === 'topic'">
              <Search class="absolute left-3 top-3.5 w-5 h-5 text-slate-500 group-focus-within:text-cyan-400 transition-colors" />
              <input
                type="text"
                v-model="topic"
                placeholder="Enter a topic (e.g. 'Quantum Computing')"
                class="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-transparent transition-all placeholder-slate-600 text-slate-200"
              />
            </template>
            <template v-else>
              <Link class="absolute left-3 top-3.5 w-5 h-5 text-slate-500 group-focus-within:text-purple-400 transition-colors" />
              <input
                type="text"
                v-model="urlInput"
                placeholder="Paste URL (e.g. https://example.com/article)"
                class="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-400/50 focus:border-transparent transition-all placeholder-slate-600 text-slate-200"
              />
            </template>
          </div>

          <div class="relative group">
            <Mail class="absolute left-3 top-3.5 w-5 h-5 text-slate-500 group-focus-within:text-pink-400 transition-colors" />
            <input
              type="email"
              v-model="email"
              placeholder="Email report (optional)"
              class="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-400/50 focus:border-transparent transition-all placeholder-slate-600 text-slate-200"
            />
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {{ error }}
        </div>

        <!-- Action Button -->
        <button
          @click="runSummary"
          :disabled="loading"
          class="w-full py-4 rounded-xl font-bold text-lg shadow-lg flex items-center justify-center space-x-2 transition-all duration-300 transform"
          :class="loading ? 'bg-slate-800 text-slate-500 cursor-not-allowed' : 'bg-gradient-to-r from-purple-600 to-cyan-400 text-slate-900 hover:scale-[1.02] hover:shadow-cyan-400/25'"
        >
          <template v-if="loading">
            <Loader2 class="w-6 h-6 animate-spin" />
            <span>Generating Summary...</span>
          </template>
          <template v-else>
            <Play class="w-5 h-5 fill-current" />
            <span>Generate Summary</span>
          </template>
        </button>

        <!-- Output Area -->
        <div v-if="output || loading" class="mt-8 transition-all duration-500" :class="output || loading ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'">
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-medium text-cyan-400 uppercase tracking-wider">
              {{ useLocalBackend ? 'Server Response' : 'AI Summary' }}
            </label>
            <button v-if="output" @click="copyText" class="text-xs text-slate-500 hover:text-slate-300">
              Copy Text
            </button>
          </div>
          <div class="bg-slate-950 rounded-xl p-5 border border-slate-800 min-h-[150px] shadow-inner custom-scrollbar overflow-y-auto max-h-96">
            <div v-if="loading" class="space-y-3 animate-pulse">
              <div class="h-2 bg-slate-800 rounded w-3/4"></div>
              <div class="h-2 bg-slate-800 rounded w-full"></div>
              <div class="h-2 bg-slate-800 rounded w-5/6"></div>
            </div>
            <div v-else class="prose prose-invert prose-sm max-w-none text-slate-300 whitespace-pre-wrap leading-relaxed">
              {{ output }}
            </div>
          </div>
        </div>
      </div>
      
      <p class="mt-6 text-slate-600 text-xs">
        Powered by {{ useLocalBackend ? 'Local Server' : 'Gemini 2.5 Flash' }} • Secure SSL Connection
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Blob Animations */
@keyframes blob {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0px, 0px) scale(1); }
}

.animate-blob {
  animation: blob 7s infinite;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #0f172a; 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #334155; 
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #475569; 
}
</style>