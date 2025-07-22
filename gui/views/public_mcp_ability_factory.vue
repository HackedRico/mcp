<template>
  <div class="is-flex is-justify-content-center" style="width: 100%;">
    <div class="box" style="width: 75%;">
      <h2 class="title is-4 has-text-primary mb-4">LLM Operation Planner</h2>
      <strong>Example Starting Prompt:</strong>
      <blockquote class="example-prompt">
        Find some abilities that constitute a stealer adversary which includes credential-access and exfiltration, then create an adversary with those abilities, then create an operation with the adversary.
      </blockquote>

      <div class="field">
        <div class="control">
          <textarea
            v-model="inputText"
            class="textarea"
            rows="4"
            placeholder="Describe the complete adversary operation you'd like to plan and execute..."
          ></textarea>
        </div>
      </div>

      <div class="is-flex is-justify-content-space-between is-align-items-center mt-4">
        <button class="button is-light is-small" @click="$emit('back')">
          ← Back
        </button>
        <button class="button is-primary" @click="handleSubmit" :disabled="!inputText || isLoading">
          <span v-if="isLoading">Planning Operation...</span>
          <span v-else>Plan & Execute</span>
        </button>
      </div>

      <div v-if="responseMessage" class="notification is-success mt-3">
        {{ responseMessage }}
      </div>
      <div v-if="errorMessage" class="notification is-danger mt-3">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, ref } from "vue"

const $api = inject("$api")
const inputText = ref('')
const responseMessage = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

async function handleSubmit() {
  responseMessage.value = ''
  errorMessage.value = ''
  isLoading.value = true
  
  try {
    let payload = { text: inputText.value, type: 'planner' }
    console.log("Submitting planner payload:", payload)
    const response = await $api.post('/plugin/mcp/execute', payload)
    responseMessage.value = response.data.message || 'Successfully planned and created operation.'
    inputText.value = ''
  } catch (err) {
    errorMessage.value = err?.response?.data?.error || 'Operation planning failed.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.example-prompt {
  border-left: 4px solid #00cc7a;
  padding: 1rem;
  background-color: #f4f4f4;
  color: #222;
  font-style: italic;
}
</style>

