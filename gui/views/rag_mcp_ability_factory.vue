<template>
  <div class="is-flex is-justify-content-center" style="width: 100%;">
    <div style="width: 75%;">

      <!-- Header + Form -->
      <div class="box">
        <div class="is-flex is-align-items-center is-justify-content-space-between mb-3">
          <h2 class="title is-4 has-text-primary mb-0">CTI-Enhanced Ability Factory</h2>
          <span class="icon is-clickable" @click="collapsibleBoxOpen = !collapsibleBoxOpen">
            <font-awesome-icon :icon="['fas', collapsibleBoxOpen ? 'minus' : 'plus']" />
          </span>
        </div>
        <div v-show="collapsibleBoxOpen">
          <!-- Form Inputs and Example Prompt -->
          <div v-if="uiPhase === 'idle' || uiPhase === 'finished'">
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
                <span v-if="isLoading">Processing...</span>
                <span v-else>Submit</span>
              </button>
            </div>
          </div>

          <div v-if="responseMessage" class="notification is-success mt-3">
            {{ responseMessage }}
          </div>
          
          <div v-if="errorMessage" class="notification is-danger mt-3">
            {{ errorMessage }}
          </div>
        </div>
        <!-- Conditional Back Button shown only when collapsibleBoxOpen is false -->
        <div v-if="!collapsibleBoxOpen" class="mb-4">
          <button class="button is-light is-small" @click="$emit('back')">
            ← Back
          </button>
        </div>
      </div>

      <!-- Polled Feedback from MLflow -->
      <div v-if="uiPhase === 'running' || uiPhase === 'finished'" class="mt-4">
        <p v-if="pollPrompt" class="is-size-5 has-text-weight-medium"><strong>Prompt: </strong> {{ pollPrompt }}</p>
        
        <p v-if="displayedStage && displayedStage.toLowerCase() !== 'completed'" class="is-size-5 has-text-weight-medium">
          <strong>Stage: </strong> {{ displayedStage }}
        </p>

        <p><strong>Status: </strong> 
          <span v-if="pollStatus === 'RUNNING'">{{ animatedStatus }}</span>
          <span v-else>{{ pollStatus }}</span>
        </p>
      </div>

      <!-- Thoughts Section -->
      <div v-if="uiPhase === 'running' || uiPhase === 'finished'" class="mt-5" v-show="thoughts.length">
        <div class="box">
          <h3 class="title is-5">Thoughts</h3>
          <div class="reasoning-box">
            <template v-for="(thought, idx) in thoughts" :key="idx">
              <div v-for="(sentence, sIdx) in splitSentences(thought)" :key="sIdx">
                <p v-if="!isInjectedSentence(sentence)" class="thought-line">• {{ sentence }}</p>

                <!-- If ability creation sentence -->
                <div v-if="sentence.includes('I have successfully created') && sentence.includes('abilities') && !sentence.includes('adversary')">
                  <div
                    v-for="(line, aIdx) in parsedAbilityLines"
                    :key="'ability-' + sIdx + '-' + aIdx"
                    class="notification is-success mt-4 is-inline-block"
                    style="margin-left: 3rem;"
                  >
                    {{ line }}
                  </div>
                  <br>
                </div>

                <!-- If adversary creation sentence -->
                <div v-if="sentence.includes('I have successfully created') && sentence.includes('adversary')">
                  <div
                    class="notification is-success mt-4 is-inline-block"
                    style="margin-left: 2rem;"
                  >
                    {{ parsedAdversaryLine }}
                    <div v-if="parsedAbilityLines.length" class="mt-2">
                      <div
                        v-for="(line, i) in parsedAbilityLines"
                        :key="'adv-ability-' + sIdx + '-' + i"
                        style="margin-left: 2rem;"
                      >
                        {{ line }}
                      </div>
                    </div>
                  </div>
                  <br>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Reasoning Section -->
      <div v-if="uiPhase === 'running' || uiPhase === 'finished'" class="mt-5" v-show="pollReasoning">
        <div class="box">
          <h3 class="title is-5">Reasoning</h3>
          <p>{{ pollReasoning }}</p>
        </div>
      </div>

    </div>
  </div>

</template>


<script setup>
import { inject, ref, watch, computed } from "vue"
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { faPlus, faMinus } from '@fortawesome/free-solid-svg-icons'

const $api = inject("$api")
const inputText = ref('')
const responseMessage = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const runId = ref(null)
const pollStatus = ref('')
const pollStage = ref('')
const pollPrompt = ref('')
const pollTrajectory = ref({})
const pollReasoning = ref('')
const pollFinalResult = ref('')
const uiPhase = ref('idle')  // 'idle' | 'running' | 'finished'
const animatedStatus = ref('RUNNING')
const parsedAbilityLines = ref([])
const parsedAdversaryLine = ref('')
const collapsibleBoxOpen = ref(true)
const stageQueue = ref([])
let stageInterval = null
const displayedStage = ref('')
let hasShownInitialMessage = false




let dotCount = 0
let dotInterval = null

// Break each thought into individual sentences
function splitSentences(thought) {
  return thought.split(/[.?!]\s+/).map(s => s.trim()).filter(Boolean)
}
function isInjectedSentence(sentence) {
  return sentence.includes('I have successfully created') && (
    sentence.includes('abilities') || sentence.includes('adversary')
  )
}


async function handleSubmit() {
  errorMessage.value = ''
  isLoading.value = true
  pollStatus.value = 'RUNNING'
  startStatusAnimation()
  uiPhase.value = 'running'
  parsedAbilityLines.value = []
  parsedAdversaryLine.value = ''
  pollPrompt.value = ''
  pollStage.value = ''
  pollReasoning.value = ''
  pollFinalResult.value = ''
  pollTrajectory.value = {}
  runId.value = null
  responseMessage.value = 'Started ability creation process.'
  displayedStage.value = ''
  hasShownInitialMessage = false
  stageQueue.value = []
  stageInterval = null
  
  try {
    if (pollInterval) clearInterval(pollInterval)
    if (stageInterval) clearInterval(stageInterval)

    let payload = { text: inputText.value, type: 'rag_factory' }
    console.log("Submitting factory payload:", payload)
    const response = await $api.post('/plugin/mcp/execute', payload)

    // ✅ Pull out run_id and start polling
    runId.value = response.data.run_id
    
    pollStatusUpdates(runId.value)
    inputText.value = ''
  } catch (err) {
    errorMessage.value = err?.response?.data?.error || 'Submission failed.'
  } finally {
    isLoading.value = false
  }
}
let pollInterval = null;
let shownStages = new Set();

function pollStatusUpdates(id) {
  if (pollInterval) clearInterval(pollInterval);
  pollStatus.value = 'RUNNING';
  startStatusAnimation();

  pollInterval = setInterval(async () => {
    try {
      const res = await $api.get('/plugin/mcp/status', { params: { run_id: id } });
      console.log('[POLL] Status response:', res.data);

      pollStatus.value = res.data.status || 'unknown';
      pollPrompt.value = res.data.prompt || '';
      pollReasoning.value = res.data.reasoning || '';
      pollFinalResult.value = res.data.process_result || '';
      pollTrajectory.value = res.data.trajectory || {};
      const traj = pollTrajectory.value;

      if (pollStatus.value === 'RUNNING') startStatusAnimation();
      else stopStatusAnimation();

      // Handle staged updates
      const stage = res.data.stage;
      const stageLower = stage?.toLowerCase();
      if (
        stage &&
        !stageLower.includes('complete') &&
        stage !== displayedStage.value &&
        !shownStages.has(stage) &&
        !stageQueue.value.includes(stage)
      ) {
        if (!displayedStage.value && stageQueue.value.length === 0 && shownStages.size === 0) {
          displayedStage.value = stage;
          shownStages.add(stage);
          console.log('[DISPLAY] First stage shown immediately:', stage);
        } else {
          stageQueue.value.push(stage);
          console.log('[QUEUE] New stage added:', stage);
        }
      }

      if (!stageInterval) {
        stageInterval = setInterval(() => {
          if (stageQueue.value.length > 0) {
            const next = stageQueue.value.shift();
            displayedStage.value = next;
            shownStages.add(next);
            console.log('[DISPLAY] Stage now showing:', next);
          }
        }, 8000);
      }

      // Terminal status
      if (pollStatus.value === 'FINISHED' || pollStatus.value === 'FAILED') {
        clearInterval(pollInterval);
        clearInterval(stageInterval);
        pollInterval = null;
        stageInterval = null;
        stageQueue.value = [];
        displayedStage.value = '';
        uiPhase.value = 'finished';
        collapsibleBoxOpen.value = false;
        responseMessage.value = 'Execution complete.';
      }

      console.log('[TRAJECTORY]', traj);
      const uuidToName = {};
      const abilityUuids = [];

      // ✅ Attempt to parse adversary creation step
      try {
        const advToolEntry = Object.entries(traj).find(
          ([k, v]) => k.startsWith('tool_name_') && v === 'create_adversary'
        );
        if (advToolEntry) {
          const idx = advToolEntry[0].split('_')[2];
          let args = traj[`tool_args_${idx}`];
          let obs = traj[`observation_${idx}`];

          try { if (typeof args === 'string') args = JSON.parse(args); } catch { args = null; }
          try { if (typeof obs === 'string') obs = JSON.parse(obs); } catch { obs = null; }

          const adversaryUUID = obs?.adversary_id || 'unknown-uuid';
          parsedAdversaryLine.value = {
            name: args?.name || 'Unnamed Adversary',
            uuid: adversaryUUID
          };

          if (Array.isArray(args?.atomic_ordering)) {
            abilityUuids.push(...args.atomic_ordering);
            console.log('[DEBUG] Found ability UUIDs from adversary:', abilityUuids);
          }
        } else {
          console.warn('[INFO] No create_adversary entry found. Skipping adversary parse.');
        }
      } catch (err) {
        console.error('[ERROR] Exception during adversary parse:', err);
      }

      // ✅ Parse all ability observations
      Object.entries(traj).forEach(([key, val]) => {
        if (!key.startsWith('observation_')) return;

        let parsed;
        try {
          parsed = typeof val === 'string' ? JSON.parse(val) : val;
        } catch {
          console.warn(`[WARN] Could not parse ${key}`);
          return;
        }

        const items = Array.isArray(parsed) ? parsed : [parsed];
        items.forEach(item => {
          if (item?.ability_id && item?.name) {
            uuidToName[item.ability_id] = item.name;
            console.debug(`[DEBUG] Observed ability: ${item.ability_id} = ${item.name}`);
          }
        });
      });

      // ✅ Pick ability lines to display
      if (abilityUuids.length > 0) {
        parsedAbilityLines.value = abilityUuids
          .map(uuid => uuidToName[uuid])
          .filter(Boolean);
        console.log('[INFO] Parsed abilities from atomic_ordering:', parsedAbilityLines.value);
      } else {
        parsedAbilityLines.value = Object.values(uuidToName).filter(Boolean);
        console.warn('[FALLBACK] Using all observed abilities (no adversary UUID list).');
      }

      // ✅ Fallback: check for any ability create tool entries
      if (parsedAbilityLines.value.length === 0) {
        Object.entries(traj).forEach(([key, val]) => {
          if (key.startsWith('tool_name_') && val.includes('create')) {
            const idx = key.split('_')[2];
            let args = traj[`tool_args_${idx}`];
            let obs = traj[`observation_${idx}`];

            try { if (typeof args === 'string') args = JSON.parse(args); } catch { args = null; }
            try { if (typeof obs === 'string') obs = JSON.parse(obs); } catch { obs = null; }

            if (args?.technique_name && obs?.ability_id && obs?.name && !uuidToName[obs.ability_id]) {
              uuidToName[obs.ability_id] = obs.name;
              parsedAbilityLines.value.push(obs.name);
              console.debug('[FALLBACK] Created ability parsed:', {
                name: obs.name,
                technique: args.technique_name
              });
            }
          }
        });
      }

      console.log('[FINAL] Abilities to show in UI:', parsedAbilityLines.value);

      // ✅ Optional: Parse operation
      try {
        const opToolEntry = Object.entries(traj).find(
          ([k, v]) => k.startsWith('tool_name_') && v === 'create_operation'
        );
        if (opToolEntry) {
          const idx = opToolEntry[0].split('_')[2];
          let args = traj[`tool_args_${idx}`];
          try { if (typeof args === 'string') args = JSON.parse(args); } catch { args = null; }

          if (args?.operation_name) {
            parsedOperationLine.value = {
              name: args.operation_name,
              adversaryName: args.adversary_name || 'unknown'
            };
            console.debug('[DEBUG] Parsed operation:', parsedOperationLine.value);
          }
        }
      } catch (err) {
        console.error('[ERROR] Exception during operation parse:', err);
      }

    } catch (e) {
      console.error('Polling error:', e);
      clearInterval(pollInterval);
      pollInterval = null;
      errorMessage.value = 'Polling failed.';
    }
  }, 1000);
}



function startStatusAnimation() {
  if (dotInterval) return  // avoid multiple intervals

  dotInterval = setInterval(() => {
    dotCount = (dotCount + 1) % 4  // 0 to 3
    animatedStatus.value = 'RUNNING' + '.'.repeat(dotCount)
  }, 500)  // adjust speed as desired
}

function stopStatusAnimation() {
  if (dotInterval) {
    clearInterval(dotInterval)
    dotInterval = null
    animatedStatus.value = pollStatus.value  // reset to actual status string
  }
}

// Extract thoughts from the trajectory object
const thoughts = computed(() => {
  const traj = pollTrajectory.value
  if (!traj) return []
  return Object.entries(traj)
    .filter(([key]) => key.startsWith("thought_"))
    .sort(([a], [b]) => {
      const getIndex = (k) => parseInt(k.match(/\d+/)?.[0] || 0)
      return getIndex(a) - getIndex(b)
    })
    .map(([_, val]) => val)
})

  watch(responseMessage, (newVal, oldVal) => {
  if (newVal && newVal !== oldVal) {
     if (!hasShownInitialMessage) {
      hasShownInitialMessage = true;
      return;  // show first message immediately
    }
    setTimeout(() => {
      if (responseMessage.value === newVal) {
        responseMessage.value = ''
      }
    }, 4000)
  }
})

</script>
<style scoped>
.example-prompt {
  border-left: 4px solid #7a00cc;
  padding: 1rem;
  background-color: #f4f4f4;
  color: #222; /* darker text for better contrast */
  font-style: italic;
}

.title.is-5 + .title.is-5 {
  margin-top: 2rem; /* Ensure vertical spacing between Thoughts and Reasoning headings */
}
.reasoning-box p {
  margin-left: 1rem; /* indent bullet-pointed sentences */
}
.reasoning-box .notification {
  margin-bottom: .5rem; /* Adjust spacing between items */
}
.icon.is-clickable i {
  color: white !important;
  font-size: 1.25rem;
}
.thought-line {
  margin-left: 1.5rem;  /* indent */
  margin-bottom: 0.5rem;  /* vertical spacing between bullets */
  line-height: 1.4;  /* slightly more legible */
}
</style>

