<script setup>
import { ref } from 'vue';
import {
  TrendingUp,
  Search,
  AlertCircle,
  CheckCircle,
  Clock,
  DollarSign
} from 'lucide-vue-next';

// --- State ---
const symbol = ref('SPY');
const isLoading = ref(false);
const signal = ref(null);
const error = ref(null);

// --- Mock Signal Data ---
const mockSignal = {
  asset: "SPY",
  direction: "LONG",
  confidence: 0.78,
  entry_target: 451.00,
  stop_loss_target: 450.25,
  take_profit_target: 452.50,
  risk_reward_ratio: 2.0,
  signal_strength: "MODERATE",
  agent_consensus: {
    chartanalyst: "BUY",
    macroagent: "BUY",
    marketsentinel: "HOLD"
  },
  confirming_factors: [
    "Strong bullish pattern",
    "Positive macro outlook"
  ],
  conflicting_factors: [
    "Mixed sentiment signals"
  ],
  risk_assessment: {
    market_risk: "MEDIUM",
    volatility_risk: "LOW",
    liquidity_risk: "LOW"
  },
  reasoning: "Bullish consensus with 2/3 agents recommending LONG positions. Overall confidence score of 0.78",
  recommendations: [
    "Consider taking position with reduced allocation",
    "Monitor position closely and adjust stop loss as needed"
  ],
  next_review_time: "Within 4 hours"
};

// --- Functions ---
const generateSignal = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await fetch('http://192.168.1.160:8000/trading/signal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol: symbol.value })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    signal.value = await response.json();
  } catch (err) {
    error.value = 'Failed to generate trading signal. Please ensure the backend server is running.';
    console.error('Signal generation error:', err);
  } finally {
    isLoading.value = false;
  }
};

const getSignalColor = (direction) => {
  return direction === 'LONG' ? 'text-green-400' : 'text-red-400';
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.75) return 'text-green-400';
  if (confidence >= 0.65) return 'text-yellow-400';
  return 'text-red-400';
};
</script>

<template>
  <div class="min-h-screen p-8 bg-slate-950 text-slate-100">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center space-x-3 mb-4">
          <TrendingUp class="w-8 h-8 text-cyan-400" />
          <h1 class="text-3xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            Trading Signals
          </h1>
        </div>
        <p class="text-slate-400">
          AI-powered trading signals with multi-agent analysis
        </p>
      </div>

      <!-- Signal Generator -->
      <div class="bg-slate-900/50 backdrop-blur-xl rounded-lg border border-slate-800 p-6 mb-8">
        <h2 class="text-xl font-semibold mb-4 text-slate-200">Generate Trading Signal</h2>

        <div class="flex gap-4 mb-4">
          <div class="flex-1">
            <label class="block text-sm font-medium text-slate-300 mb-2">
              Symbol
            </label>
            <input
              v-model="symbol"
              type="text"
              placeholder="e.g., SPY, AAPL, ZAR=X"
              class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
          </div>
          <div class="flex items-end">
            <button
              @click="generateSignal"
              :disabled="isLoading"
              class="px-6 py-2 bg-gradient-to-r from-purple-600 to-cyan-400 text-slate-900 font-bold rounded-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Search v-if="!isLoading" class="w-5 h-5 inline mr-2" />
              <Clock v-if="isLoading" class="w-5 h-5 inline mr-2 animate-spin" />
              {{ isLoading ? 'Generating...' : 'Generate Signal' }}
            </button>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="flex items-center space-x-2 text-red-400 bg-red-900/20 border border-red-800 rounded-lg p-4">
          <AlertCircle class="w-5 h-5" />
          <span>{{ error }}</span>
        </div>
      </div>

      <!-- Signal Display -->
      <div v-if="signal" class="bg-slate-900/50 backdrop-blur-xl rounded-lg border border-slate-800 p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <CheckCircle class="w-6 h-6 text-green-400" />
            <h2 class="text-2xl font-bold text-slate-200">Signal Generated</h2>
          </div>
          <div class="text-right">
            <div class="text-2xl font-bold" :class="getSignalColor(signal.direction)">
              {{ signal.direction }}
            </div>
            <div class="text-sm text-slate-400">{{ signal.asset }}</div>
          </div>
        </div>

        <!-- Key Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-slate-800/50 rounded-lg p-4">
            <div class="flex items-center space-x-2 mb-2">
              <TrendingUp class="w-4 h-4 text-cyan-400" />
              <span class="text-sm font-medium text-slate-300">Confidence</span>
            </div>
            <div class="text-2xl font-bold" :class="getConfidenceColor(signal.confidence)">
              {{ (signal.confidence * 100).toFixed(1) }}%
            </div>
          </div>

          <div class="bg-slate-800/50 rounded-lg p-4">
            <div class="flex items-center space-x-2 mb-2">
              <DollarSign class="w-4 h-4 text-green-400" />
              <span class="text-sm font-medium text-slate-300">Entry Price</span>
            </div>
            <div class="text-2xl font-bold text-slate-100">
              ${{ signal.entry_target.toFixed(2) }}
            </div>
          </div>

          <div class="bg-slate-800/50 rounded-lg p-4">
            <div class="flex items-center space-x-2 mb-2">
              <AlertCircle class="w-4 h-4 text-red-400" />
              <span class="text-sm font-medium text-slate-300">Stop Loss</span>
            </div>
            <div class="text-2xl font-bold text-slate-100">
              ${{ signal.stop_loss_target.toFixed(2) }}
            </div>
          </div>

          <div class="bg-slate-800/50 rounded-lg p-4">
            <div class="flex items-center space-x-2 mb-2">
              <TrendingUp class="w-4 h-4 text-purple-400" />
              <span class="text-sm font-medium text-slate-300">Risk/Reward</span>
            </div>
            <div class="text-2xl font-bold text-slate-100">
              {{ signal.risk_reward_ratio }}:1
            </div>
          </div>
        </div>

        <!-- Agent Consensus -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold text-slate-200 mb-3">Agent Consensus</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div v-for="(opinion, agent) in signal.agent_consensus" :key="agent"
                 class="bg-slate-800/50 rounded-lg p-4">
              <div class="text-sm font-medium text-slate-300 capitalize mb-1">{{ agent }}</div>
              <div class="text-lg font-bold"
                   :class="opinion === 'BUY' ? 'text-green-400' : opinion === 'SELL' ? 'text-red-400' : 'text-yellow-400'">
                {{ opinion }}
              </div>
            </div>
          </div>
        </div>

        <!-- Reasoning -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold text-slate-200 mb-3">Analysis</h3>
          <p class="text-slate-300 leading-relaxed">{{ signal.reasoning }}</p>
        </div>

        <!-- Factors -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h4 class="text-md font-semibold text-green-400 mb-3">Confirming Factors</h4>
            <ul class="space-y-2">
              <li v-for="factor in signal.confirming_factors" :key="factor"
                  class="flex items-start space-x-2">
                <CheckCircle class="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <span class="text-slate-300">{{ factor }}</span>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="text-md font-semibold text-yellow-400 mb-3">Conflicting Factors</h4>
            <ul class="space-y-2">
              <li v-for="factor in signal.conflicting_factors" :key="factor"
                  class="flex items-start space-x-2">
                <AlertCircle class="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                <span class="text-slate-300">{{ factor }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Recommendations -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold text-slate-200 mb-3">Recommendations</h3>
          <ul class="space-y-2">
            <li v-for="rec in signal.recommendations" :key="rec"
                class="flex items-start space-x-2">
              <CheckCircle class="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
              <span class="text-slate-300">{{ rec }}</span>
            </li>
          </ul>
        </div>

        <!-- Risk Assessment -->
        <div class="bg-slate-800/50 rounded-lg p-4">
          <h3 class="text-lg font-semibold text-slate-200 mb-3">Risk Assessment</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span class="text-sm text-slate-400">Market Risk</span>
              <div class="text-lg font-bold text-slate-100">{{ signal.risk_assessment.market_risk }}</div>
            </div>
            <div>
              <span class="text-sm text-slate-400">Volatility Risk</span>
              <div class="text-lg font-bold text-slate-100">{{ signal.risk_assessment.volatility_risk }}</div>
            </div>
            <div>
              <span class="text-sm text-slate-400">Liquidity Risk</span>
              <div class="text-lg font-bold text-slate-100">{{ signal.risk_assessment.liquidity_risk }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Placeholder when no signal -->
      <div v-else-if="!isLoading" class="bg-slate-900/50 backdrop-blur-xl rounded-lg border border-slate-800 p-12 text-center">
        <TrendingUp class="w-16 h-16 text-slate-600 mx-auto mb-4" />
        <h3 class="text-xl font-semibold text-slate-400 mb-2">No Signal Generated</h3>
        <p class="text-slate-500">Enter a symbol above and click "Generate Signal" to get AI-powered trading analysis.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional styles if needed */
</style>