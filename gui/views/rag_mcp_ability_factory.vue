<template>
  <div class="is-flex is-justify-content-center" style="width: 100%;">
    <div class="box" style="width: 75%;">
      <h2 class="title is-4 has-text-primary mb-4">Caldera Ability Factory Prompt</h2>
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

      <div class="control mt-2">
        <button class="button is-primary" @click="handleSubmit" :disabled="!inputText">
          Submit
        </button>
      </div>

      <div class="mb-3">
        <button class="button is-light is-small" @click="$emit('back')">
          ← Back
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

async function handleSubmit() {
  responseMessage.value = ''
  errorMessage.value = ''
  try {
    const response = await $api.post('/plugin/mcp/execute', { text: inputText.value })
    responseMessage.value = response.data.message || 'Successfully submitted prompt.'
    inputText.value = ''
  } catch (err) {
    errorMessage.value = err?.response?.data?.error || 'Submission failed.'
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

