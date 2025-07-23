<template>
  <div class="is-flex is-justify-content-center" style="width: 100%;">
    <div class="box" style="width: 75%;">
      <h2 class="title is-4 has-text-primary mb-4">CTI-Enhanced Ability Factory</h2>
      <strong>Example Starting Prompt:</strong>
      <blockquote class="example-prompt">
        Create abilities that mimic APT28's persistence techniques, focusing on WMI and registry modifications.
      </blockquote>

      <div class="field">
        <div class="control">
          <textarea
            v-model="inputText"
            class="textarea"
            rows="4"
            placeholder="Describe abilities based on real threat actors or techniques..."
          ></textarea>
        </div>
      </div>

      <div class="is-flex is-justify-content-space-between is-align-items-center mt-4">
        <button class="button is-light is-small" @click="$emit('back')">
          ← Back
        </button>
        <button class="button is-primary" @click="handleSubmit" :disabled="!inputText || isLoading">
          <span v-if="isLoading">Creating with CTI...</span>
          <span v-else>Create with CTI</span>
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
    let payload = { text: inputText.value, type: 'rag_factory' }
    console.log("Submitting RAG factory payload:", payload)
    const response = await $api.post('/plugin/mcp/execute', payload)
    responseMessage.value = response.data.message || 'Successfully created CTI-based abilities and adversary.'
    inputText.value = ''
  } catch (err) {
    errorMessage.value = err?.response?.data?.error || 'CTI-enhanced creation failed.'
  } finally {
    isLoading.value = false
  }
}
</script>
<style scoped>
.example-prompt {
  border-left: 4px solid #cc7a00;
  padding: 1rem;
  background-color: #f4f4f4;
  color: #222;
  font-style: italic;
}
</style>

