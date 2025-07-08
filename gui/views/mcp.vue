<template>
  <div class="content">
    <h2 class="title is-3">MCP:Factory</h2>
    <hr />

    <div v-if="!showPrompt" class="is-flex is-align-items-center is-justify-content-center">
      <div class="card p-4 m-4" style="max-width: 600px; width: 100%;">
        <div class="mb-4">
          <p>
            MCP showcases an LLM acting as a Caldera ability developer, creating new abilities where needed on the spot.
          </p>
        </div>
        <button class="button is-primary is-large mt-3" @click="showPrompt = true">
          Start MCP Session
        </button>
      </div>
    </div>

    <McpPrompt v-else />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import McpPrompt from './mcp_ability_factory.vue'  // assuming it's in the same folder
const showPrompt = ref(false)

</script>

