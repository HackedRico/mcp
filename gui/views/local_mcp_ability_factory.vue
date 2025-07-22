<template>
  <div class="is-flex is-justify-content-center" style="width: 100%;">
    <div class="box" style="width: 75%;">
      <h2 class="title is-4 has-text-primary mb-4">LLM Ability Factory</h2>
      <strong>Example Starting Prompt:</strong>
      <blockquote class="example-prompt">
        I want to create a few abilities related to persistence with WMI for Windows, then create an adversary with those abilities. Please create more than one ability.
      </blockquote>

      <div class="field">
        <div class="control">
          <textarea
            v-model="inputText"
            class="textarea"
            rows="4"
            placeholder="Describe the adversary or abilities you'd like to create..."
          ></textarea>
        </div>
      </div>

    <div class="is-flex is-justify-content-space-between is-align-items-center mt-4">
      <button class="button is-light is-small" @click="$emit('back')">
        ← Back
      </button>
      <button class="button is-primary" @click="handleSubmit" :disabled="!inputText || isLoading">
        <span v-if="isLoading">Processing...</span>
        <span v-else>Submit</span>
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
    let payload = { text: inputText.value, type: 'factory' }
    console.log("Submitting factory payload:", payload)
    const response = await $api.post('/plugin/mcp/execute', payload)
    responseMessage.value = response.data.message || 'Successfully created abilities and adversary.'
    inputText.value = ''
  } catch (err) {
    errorMessage.value = err?.response?.data?.error || 'Submission failed.'
  } finally {
    isLoading.value = false
  }
}
</script>
<style scoped>
.example-prompt {
  border-left: 4px solid #7a00cc;
  padding: 1rem;
  background-color: #f4f4f4;
  color: #222; /* darker text for better contrast */
  font-style: italic;
}
</style>

