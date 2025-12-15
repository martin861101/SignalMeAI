<script setup>
import { ref } from 'vue';
import {
  Home,
  Search,
  BookOpen,
  BarChart3,
  Menu,
  X,
  Sparkles,
  TrendingUp
} from 'lucide-vue-next';
import Researcher from './components/Researcher.vue';
import Trading from './components/Trading.vue';

// --- Navigation State ---
const activeTab = ref('researcher');
const sidebarOpen = ref(false);

// --- Navigation Items ---
const navItems = [
  { id: 'home', name: 'Home', icon: Home },
  { id: 'researcher', name: 'Researcher', icon: Search },
  { id: 'trader', name: 'Trader', icon: TrendingUp },
  { id: 'analytics', name: 'Analytics', icon: BarChart3 }
];
</script>

<template>
  <div class="min-h-screen flex bg-slate-950 text-slate-100">
    
    <!-- Mobile Menu Button -->
    <button 
      @click="sidebarOpen = !sidebarOpen"
      class="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-400 transition-colors"
    >
      <Menu v-if="!sidebarOpen" class="w-6 h-6" />
      <X v-else class="w-6 h-6" />
    </button>

    <!-- Sidebar -->
    <aside 
      class="fixed lg:static inset-y-0 left-0 z-40 w-64 bg-slate-900/95 backdrop-blur-xl border-r border-slate-800 transform transition-transform duration-300 lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="flex flex-col h-full">
        <!-- Logo -->
        <div class="p-6 border-b border-slate-800">
          <div class="flex items-center space-x-2">
            <Sparkles class="w-7 h-7 text-cyan-400" />
            <span class="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              Martin's AI Hub
            </span>
          </div>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 p-4 space-y-2">
          <button
            v-for="item in navItems"
            :key="item.id"
            @click="activeTab = item.id; sidebarOpen = false"
            class="w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200"
            :class="activeTab === item.id 
              ? 'bg-gradient-to-r from-purple-600/20 to-cyan-600/20 text-cyan-400 border border-cyan-500/30' 
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'"
          >
            <component :is="item.icon" class="w-5 h-5" />
            <span class="font-medium">{{ item.name }}</span>
          </button>
        </nav>

        <!-- Footer -->
        <div class="p-4 border-t border-slate-800">
          <div class="text-xs text-slate-600">
            <p>Version 1.0.0</p>
            <p class="mt-1">© 2025 Hookitup Services</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Overlay for mobile -->
    <div 
      v-if="sidebarOpen"
      @click="sidebarOpen = false"
      class="fixed inset-0 bg-black/50 z-30 lg:hidden"
    ></div>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto">
      <!-- Home Tab -->
      <div v-if="activeTab === 'home'" class="min-h-screen flex items-center justify-center p-8">
        <div class="text-center max-w-2xl">
          <Sparkles class="w-16 h-16 text-cyan-400 mx-auto mb-4" />
          <h1 class="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-pink-500 to-cyan-400 bg-clip-text text-transparent">
            Welcome to Martin's AI Hub
          </h1>
          <p class="text-xl text-slate-400 mb-8">
            Your AI-powered research assistant for instant knowledge distillation
          </p>
          <button
            @click="activeTab = 'researcher'"
            class="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-400 text-slate-900 font-bold rounded-lg hover:scale-105 transition-transform"
          >
            Start Researching
          </button>
        </div>
      </div>

      <!-- Researcher Tab -->
      <div v-if="activeTab === 'researcher'">
        <Researcher />
      </div>

       <!-- Trader Tab -->
       <div v-if="activeTab === 'trader'">
         <Trading />
       </div>

      <!-- Analytics Tab -->
      <div v-if="activeTab === 'analytics'" class="min-h-screen flex items-center justify-center p-8">
        <div class="text-center">
          <BarChart3 class="w-16 h-16 text-cyan-400 mx-auto mb-4" />
          <h2 class="text-3xl font-bold text-slate-200 mb-2">Analytics</h2>
          <p class="text-slate-400">Track your research activity and insights</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* No additional styles needed - handled by components */
</style>