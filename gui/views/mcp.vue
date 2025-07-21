<template>
  <div class="content">
    <h2 class="title is-3">Caldera MCP:Factory</h2>
    <hr />

    <div
      v-if="!selectedPath"
      class="is-flex m-4"
      style="gap: 1.5rem; justify-content: center; flex-wrap: wrap;"
    >
      <!-- Local -->
      <div class="box" style="flex: 1 1 300px; max-width: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="flex-grow: 1;">
          <h3 class="title is-5">Local Ability Factory</h3>
          <p>
            This MCP showcases an LLM acting as a Caldera ability developer, creating new abilities from those found locally.
          </p>
        </div>
        <div class="is-flex is-justify-content-center mt-5">
          <button class="button is-primary is-large" @click="selectedPath = 'local'">
            Start MCP Session
          </button>
        </div>
      </div>

      <!-- Public -->
      <div class="box" style="flex: 1 1 300px; max-width: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="flex-grow: 1;">
          <h3 class="title is-5">Public Ability Factory</h3>
          <p>
            This MCP showcases an LLM acting as a Caldera ability developer, creating new abilities from those found publicly.
          </p>
        </div>
        <div class="is-flex is-justify-content-center mt-5">
          <button class="button is-primary is-large" @click="selectedPath = 'public'">
            Start MCP Session
          </button>
        </div>
      </div>

      <!-- RAG -->
      <div class="box" style="flex: 1 1 300px; max-width: 320px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="flex-grow: 1;">
          <h3 class="title is-5">Ability Factory with RAG</h3>
          <p>
            This MCP showcases an LLM acting as a Caldera ability developer, incorporating CTI and a RAG.
          </p>
        </div>
        <div class="is-flex is-justify-content-center mt-5">
          <button class="button is-primary is-large" @click="selectedPath = 'rag'">
            Start MCP Session
          </button>
        </div>
      </div>
    </div>

    <McpPromptlocal v-if="selectedPath === 'local'" />
    <McpPromptpublic v-if="selectedPath === 'public'" />
    <McpPromptrag v-if="selectedPath === 'rag'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import McpPromptlocal from './local_mcp_ability_factory.vue'
import McpPromptpublic from './public_mcp_ability_factory.vue'
import McpPromptrag from './rag_mcp_ability_factory.vue'
const selectedPath = ref(null)
</script>
