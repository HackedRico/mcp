<template>
  <div class="content">
    <h2 class="title is-3">Caldera MCP: AI-Powered Operations</h2>
    <hr />

    <div
      v-if="!selectedPath"
      class="is-flex m-4"
      style="gap: 1.5rem; justify-content: center; flex-wrap: wrap;"
    >
      <!-- LLM Factory -->
      <div class="box" style="flex: 1 1 300px; max-width: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="flex-grow: 1;">
          <h3 class="title is-5">LLM Ability Factory</h3>
          <p>
            AI creates new abilities and adversaries based on your descriptions. Best for creating specific capabilities.
          </p>
        </div>
        <div class="is-flex is-justify-content-center mt-5">
          <button class="button is-primary is-large" @click="selectedPath = 'factory'">
            Start Factory Session
          </button>
        </div>
      </div>

      <!-- LLM Planner -->
      <div class="box" style="flex: 1 1 300px; max-width: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="flex-grow: 1;">
          <h3 class="title is-5">LLM Operation Planner</h3>
          <p>
            AI plans and executes complete adversary operations. Best for comprehensive attack scenarios.
          </p>
        </div>
        <div class="is-flex is-justify-content-center mt-5">
          <button class="button is-primary is-large" @click="selectedPath = 'planner'">
            Start Planner Session
          </button>
        </div>
      </div>

      <!-- RAG Factory -->
      <div class="box" style="flex: 1 1 300px; max-width: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="flex-grow: 1;">
          <h3 class="title is-5">CTI-Enhanced Factory</h3>
          <p>
            AI creates abilities using real-world threat intelligence data. Best for realistic threat emulation.
          </p>
        </div>
        <div class="is-flex is-justify-content-center mt-5">
          <button class="button is-primary is-large" @click="selectedPath = 'rag_factory'">
            Start CTI Factory
          </button>
        </div>
      </div>

      <!-- RAG Planner -->
      <div class="box" style="flex: 1 1 300px; max-width: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="flex-grow: 1;">
          <h3 class="title is-5">CTI-Enhanced Planner</h3>
          <p>
            AI plans operations based on real threat actor behaviors. Best for authentic adversary simulations.
          </p>
        </div>
        <div class="is-flex is-justify-content-center mt-5">
          <button class="button is-primary is-large" @click="selectedPath = 'rag_planner'">
            Start CTI Planner
          </button>
        </div>
      </div>
    </div>

    <McpPromptFactory v-if="selectedPath === 'factory'" @back="selectedPath = null" />
    <McpPromptPlanner v-if="selectedPath === 'planner'" @back="selectedPath = null" />
    <McpPromptRAGFactory v-if="selectedPath === 'rag_factory'" @back="selectedPath = null" />
    <McpPromptRAGPlanner v-if="selectedPath === 'rag_planner'" @back="selectedPath = null" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import McpPromptFactory from './local_mcp_ability_factory.vue'
import McpPromptPlanner from './public_mcp_ability_factory.vue'
import McpPromptRAGFactory from './rag_mcp_ability_factory.vue'
import McpPromptRAGPlanner from './rag_mcp_planner.vue'

const selectedPath = ref(null)
</script>
