<script setup>
import { ref } from 'vue';
import {
  TrendingUp,
  Search,
  AlertCircle,
  CheckCircle,
  Clock,
  DollarSign,
  Calendar,
  Globe
} from 'lucide-vue-next';

// --- State ---
const symbol = ref('XAUUSD'); // Defaulting to Gold/Silver per your interest
const isLoading = ref(false);
const signal = ref(null);
const error = ref(null);
const backendUrl = ref('http://localhost:8000'); // Configurable backend URL

// --- API Function ---
const generateSignal = async () => {
  isLoading.value = true;
  error.value = null;
  signal.value = null;

  try {
    const response = await fetch(`${backendUrl.value}/trading/signal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol: symbol.value })
    });

    if (!response.ok) {
      throw new Error(`Server Error: ${response.status}`);
    }

    signal.value = await response.json();
  } catch (err) {
    error.value = `Failed to connect to backend at ${backendUrl.value}. Is the MCP server running?`;
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

// --- Helpers ---
const getSignalColor = (direction) => {
  if (direction === 'LONG') return 'text-green-400';
  if (direction === 'SHORT') return 'text-red-400';
  return 'text-yellow-400';
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.75) return 'text-green-400';
  if (confidence >= 0.60) return 'text-yellow-400';
  return 'text-red-400';
};
</script>

<template>
  <div class="min-h-screen p-8 bg-slate-950 text-slate-100 font-sans">
    <div class="max-w-6xl mx-auto">
      
       <div class="mb-8">
         <div class="flex items-center space-x-3 mb-4">
           <TrendingUp class="w-8 h-8 text-cyan-400" />
           <h1 class="text-3xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
             ApexAI Aura Insight
           </h1>
         </div>
         <p class="text-slate-400 mb-2">
           Multi-Agent Trading Signal Generation: Chart Analysis, Macro Economics, Market Sentiment
         </p>
         <div class="text-xs text-slate-500 space-y-1">
           <p>• <strong>ChartAnalyst:</strong> Technical analysis with pivot detection and Fibonacci patterns</p>
           <p>• <strong>MacroAgent:</strong> Economic calendar monitoring and central bank policy analysis</p>
           <p>• <strong>MarketSentinel:</strong> Social sentiment and market flow analysis</p>
           <p>• <strong>PlatformPilot:</strong> Signal synthesis and risk management</p>
         </div>
       </div>

       <div class="bg-slate-900/50 backdrop-blur-xl rounded-lg border border-slate-800 p-6 mb-8 shadow-lg">
         <h2 class="text-xl font-semibold mb-4 text-slate-200">Signal Generator</h2>

         <!-- Backend Configuration -->
         <div class="mb-4 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
           <label class="block text-sm font-medium text-slate-300 mb-2">Backend URL</label>
           <input
             v-model="backendUrl"
             type="text"
             placeholder="http://localhost:8000"
             class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all text-sm"
           />
           <p class="text-xs text-slate-500 mt-1">MCP server endpoint for trading signals</p>
         </div>

         <div class="flex gap-4 mb-4">
           <div class="flex-1">
             <label class="block text-sm font-medium text-slate-300 mb-2">Symbol</label>
             <input
               v-model="symbol"
               type="text"
               placeholder="e.g., XAUUSD, EURUSD, SPY, GC=F"
               class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all"
               @keyup.enter="generateSignal"
             />
           </div>
           <div class="flex items-end">
             <button
               @click="generateSignal"
               :disabled="isLoading"
               class="px-6 py-2 bg-gradient-to-r from-purple-600 to-cyan-400 text-slate-900 font-bold rounded-lg hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100 flex items-center"
             >
               <Search v-if="!isLoading" class="w-5 h-5 mr-2" />
               <Clock v-else class="w-5 h-5 mr-2 animate-spin" />
               {{ isLoading ? 'Analyzing...' : 'Generate Signal' }}
             </button>
           </div>
         </div>
         <div v-if="error" class="flex items-center space-x-2 text-red-400 bg-red-900/20 border border-red-800 rounded-lg p-4">
           <AlertCircle class="w-5 h-5" />
           <div>
             <span class="font-medium">{{ error }}</span>
             <p class="text-sm text-red-300 mt-1">
               Make sure the MCP server is running: <code class="bg-red-900/50 px-2 py-1 rounded text-xs">cd mcp && python server.py</code>
             </p>
           </div>
         </div>

         <!-- System Status -->
         <div class="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
           <h3 class="text-sm font-medium text-slate-300 mb-2">System Status</h3>
           <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
             <div class="flex items-center space-x-2">
               <div class="w-2 h-2 rounded-full bg-green-400"></div>
               <span class="text-slate-400">ChartAnalyst</span>
             </div>
             <div class="flex items-center space-x-2">
               <div class="w-2 h-2 rounded-full bg-green-400"></div>
               <span class="text-slate-400">MacroAgent</span>
             </div>
             <div class="flex items-center space-x-2">
               <div class="w-2 h-2 rounded-full bg-green-400"></div>
               <span class="text-slate-400">MarketSentinel</span>
             </div>
             <div class="flex items-center space-x-2">
               <div class="w-2 h-2 rounded-full bg-green-400"></div>
               <span class="text-slate-400">PlatformPilot</span>
             </div>
           </div>
           <p class="text-xs text-slate-500 mt-2">All agents active with Ollama LLM fallback</p>
         </div>
      </div>

      <div v-if="signal" class="animate-fade-in space-y-6">
        
        <div class="bg-slate-900/80 backdrop-blur-xl rounded-lg border border-slate-700 p-6 shadow-2xl">
          <div class="flex items-center justify-between mb-6 pb-6 border-b border-slate-700">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-full bg-slate-800">
                <Globe class="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <h2 class="text-2xl font-bold text-slate-200">{{ signal.asset }}</h2>
                <span class="text-xs text-slate-400 uppercase tracking-wider">AI Consensus</span>
              </div>
            </div>
            <div class="text-right">
              <div class="text-3xl font-black tracking-tight" :class="getSignalColor(signal.direction)">
                {{ signal.direction }}
              </div>
              <div class="text-sm text-slate-400">Recommendation</div>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
              <div class="flex items-center space-x-2 mb-2">
                <TrendingUp class="w-4 h-4 text-cyan-400" />
                <span class="text-sm font-medium text-slate-400">Confidence</span>
              </div>
              <div class="text-2xl font-bold" :class="getConfidenceColor(signal.confidence)">
                {{ (signal.confidence * 100).toFixed(0) }}%
              </div>
            </div>
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
              <div class="flex items-center space-x-2 mb-2">
                <DollarSign class="w-4 h-4 text-blue-400" />
                <span class="text-sm font-medium text-slate-400">Entry</span>
              </div>
              <div class="text-2xl font-bold text-slate-100">
                ${{ signal.entry_target.toFixed(2) }}
              </div>
            </div>
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
              <div class="flex items-center space-x-2 mb-2">
                <AlertCircle class="w-4 h-4 text-red-400" />
                <span class="text-sm font-medium text-slate-400">Stop Loss</span>
              </div>
              <div class="text-2xl font-bold text-slate-100">
                ${{ signal.stop_loss_target.toFixed(2) }}
              </div>
            </div>
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
              <div class="flex items-center space-x-2 mb-2">
                <CheckCircle class="w-4 h-4 text-green-400" />
                <span class="text-sm font-medium text-slate-400">Take Profit</span>
              </div>
              <div class="text-2xl font-bold text-slate-100">
                ${{ signal.take_profit_target.toFixed(2) }}
              </div>
            </div>
          </div>

           <div class="mb-6">
             <h3 class="text-lg font-semibold text-slate-200 mb-3">Agent Consensus</h3>
             <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
               <div v-for="(opinion, agent) in signal.agent_consensus" :key="agent" class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/30">
                 <div class="text-sm font-medium text-slate-400 capitalize mb-1">
                   {{ agent === 'chartanalyst' ? 'Chart Analyst' : agent === 'macroagent' ? 'Macro Agent' : agent === 'marketsentinel' ? 'Market Sentinel' : agent }}
                 </div>
                 <div class="text-lg font-bold" :class="getSignalColor(opinion)">{{ opinion }}</div>
                 <div class="text-xs text-slate-500 mt-1">
                   {{ agent === 'chartanalyst' ? 'Technical Analysis' : agent === 'macroagent' ? 'Economic Analysis' : agent === 'marketsentinel' ? 'Sentiment Analysis' : 'Signal Synthesis' }}
                 </div>
               </div>
             </div>
           </div>

           <!-- Reasoning and Recommendations -->
           <div v-if="signal.reasoning || signal.recommendations" class="mb-6 space-y-4">
             <div v-if="signal.reasoning" class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/30">
               <h3 class="text-lg font-semibold text-slate-200 mb-2">Analysis Reasoning</h3>
               <p class="text-slate-300 text-sm">{{ signal.reasoning }}</p>
             </div>

             <div v-if="signal.recommendations && signal.recommendations.length > 0" class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/30">
               <h3 class="text-lg font-semibold text-slate-200 mb-2">Trading Recommendations</h3>
               <ul class="space-y-1">
                 <li v-for="(rec, idx) in signal.recommendations" :key="idx" class="text-slate-300 text-sm flex items-start">
                   <span class="text-cyan-400 mr-2">•</span>
                   {{ rec }}
                 </li>
               </ul>
             </div>
           </div>
        </div>

        <div v-if="signal.macro_events && signal.macro_events.length > 0" class="bg-slate-900/80 backdrop-blur-xl rounded-lg border border-slate-700 p-6 shadow-xl">
          <div class="flex items-center space-x-3 mb-4">
            <Calendar class="w-6 h-6 text-red-400" />
            <h3 class="text-xl font-bold text-slate-200">High Impact Economic Events</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-slate-300">
              <thead class="bg-slate-800/50 text-xs uppercase text-slate-400">
                <tr>
                  <th class="px-4 py-3">Date</th>
                  <th class="px-4 py-3">Time</th>
                  <th class="px-4 py-3">Currency</th>
                  <th class="px-4 py-3">Event</th>
                  <th class="px-4 py-3">Forecast</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-700">
                <tr v-for="(event, idx) in signal.macro_events" :key="idx" class="hover:bg-slate-800/30 transition-colors">
                  <td class="px-4 py-3 font-medium">{{ event.date }}</td>
                  <td class="px-4 py-3">{{ event.time }}</td>
                  <td class="px-4 py-3 font-bold text-slate-200">{{ event.currency }}</td>
                  <td class="px-4 py-3 text-red-300 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                    {{ event.event }}
                  </td>
                  <td class="px-4 py-3">{{ event.forecast }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="bg-slate-900/50 rounded-lg border border-slate-800 p-6 text-center text-slate-500">
          <CheckCircle class="w-8 h-8 mx-auto mb-2 opacity-50" />
          No High-Impact events detected for the next 3 days.
        </div>

      </div>
    </div>
  </div>
</template>