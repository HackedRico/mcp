<template>
  <div class="is-flex is-justify-content-center" style="width: 100%;">
    <div style="width: 75%;">

      <!-- Header + Form -->
      <div class="box">
        <div class="is-flex is-align-items-center is-justify-content-space-between mb-3">
          <h2 class="title is-4 has-text-primary mb-0">LLM Operation Planner</h2>
          <span class="icon is-clickable" @click="collapsibleBoxOpen = !collapsibleBoxOpen">
            <font-awesome-icon :icon="['fas', collapsibleBoxOpen ? 'minus' : 'plus']" />
          </span>
        </div>
        <div v-show="collapsibleBoxOpen">
          <!-- Form Inputs and Example Prompt -->
          <div v-if="uiPhase === 'idle' || uiPhase === 'finished'">
            <strong>Example Starting Prompt:</strong>
      <blockquote class="example-prompt">
        Find some abilities that constitute a stealer adversary for linux which includes credential-access and exfiltration, then create an adversary with those abilities, then create an operation with the adversary.
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
                <div v-if="lastAbilitySentenceKeys.has(`${idx}-${sIdx}`)">
                  <div
                    v-for="(line, aIdx) in parsedAbilityLines"
                    :key="'ability-' + sIdx + '-' + aIdx"
                    class="notification is-success mt-4"
                    style="margin-left: 3rem; display: table; padding: 0.75rem 1.25rem; border-radius: 8px;"
                  >
                    {{ line }}
                  </div>
                  <br>
                </div>

                <!-- If adversary creation sentence -->
                <div v-if="lastAdversarySentenceKeys.has(`${idx}-${sIdx}`)">
                  <div
                    class="notification is-success mt-4 is-inline-block"
                    style="margin-left: 2rem;"
                  >
                    {{ parsedAdversaryLine.name }} - {{ parsedAdversaryLine.uuid }}
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

                <!-- If operation creation sentence -->
                <div v-if="lastOperationSentenceKeys.has(`${idx}-${sIdx}`)">
                  <div
                    class="notification is-info mt-4"
                    style="margin-left: 2rem;"
                  >
                    {{ parsedOperationLine.name }}
                  </div>
                </div>
                <br>
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
const parsedOperationLine = ref('');





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
  responseMessage.value = 'Started Creation of the Operation.'
  displayedStage.value = ''
  hasShownInitialMessage = false
  stageQueue.value = []
  stageInterval = null
  
  try {
    if (pollInterval) clearInterval(pollInterval)
    if (stageInterval) clearInterval(stageInterval)

    let payload = { text: inputText.value, type: 'planner' }

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

      if (pollStatus.value === 'RUNNING') {
        startStatusAnimation();
      } else {
        stopStatusAnimation();
      }

      const stage = res.data.stage;
      const stageLower = stage?.toLowerCase();

      // ✅ Queue unseen, non-duplicate stages only
      if (
        stage &&
        !stageLower.includes('complete') &&
        stage !== displayedStage.value &&
        !shownStages.has(stage) &&
        !stageQueue.value.includes(stage)
      ) {
        // If this is the first stage, show immediately
        if (!displayedStage.value && stageQueue.value.length === 0 && shownStages.size === 0) {
          displayedStage.value = stage;
          shownStages.add(stage);
          console.log('[DISPLAY] First stage shown immediately:', stage);
        } else {
          stageQueue.value.push(stage);
          console.log('[QUEUE] New stage added:', stage);
        }
      }


      // ✅ Stage displayer: every 8s, show one new stage
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

      // ✅ Exit condition
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

      // ✅ Post-processing logic (unchanged, keep this as-is)
      const traj = res.data.trajectory;
      if (!traj) {
        console.warn('[WARN] No trajectory found in response.');
        return;
      }

      const advToolEntry = Object.entries(traj).find(
        ([k, v]) => k.startsWith('tool_name_') && v === 'create_adversary'
      );
      if (!advToolEntry) {
        console.warn('[WARN] No create_adversary tool_name_X entry found.');
        return;
      }

      const idx = advToolEntry[0].split('_')[2];
      let args = traj[`tool_args_${idx}`];
      let observation = traj[`observation_${idx}`];

      try {
        if (typeof args === 'string') args = JSON.parse(args);
      } catch {
        console.warn('[WARN] Failed to parse tool_args:', args);
        return;
      }

      if (!args || !Array.isArray(args.atomic_ordering)) {
        console.warn('[WARN] Invalid atomic_ordering in tool_args:', args);
        return;
      }

      let adversaryUUID = null;
      try {
        const parsedObs = typeof observation === 'string' ? JSON.parse(observation) : observation;
        adversaryUUID = parsedObs?.adversary_id || null;
        console.log('[DEBUG] Parsed adversary UUID from observation:', adversaryUUID);
      } catch {
        console.warn('[WARN] Failed to parse observation:', observation);
      }

      parsedAdversaryLine.value = {
        name: args.name || 'Unnamed Adversary',
        uuid: adversaryUUID || 'unknown-uuid'
      };

      const abilityUuids = args.atomic_ordering;
      const uuidToName = {};

      Object.entries(traj)
        .filter(([k]) => k.startsWith('observation_'))
        .forEach(([k, v]) => {
          let parsed;
          try {
            parsed = typeof v === 'string' ? JSON.parse(v) : v;
          } catch {
            console.warn(`[WARN] Could not parse ${k}`);
            return;
          }

          if (parsed?.ability_id && parsed?.name) {
            uuidToName[parsed.ability_id] = parsed.name;
          }

          if (Array.isArray(parsed)) {
            parsed.forEach(item => {
              let obj;
              try {
                obj = typeof item === 'string' ? JSON.parse(item) : item;
              } catch {
                return;
              }
              if (obj?.ability_id && obj?.name) {
                uuidToName[obj.ability_id] = obj.name;
              }
            });
          }
        });

      parsedAbilityLines.value = abilityUuids
        .map(uuid => {
          const name = uuidToName[uuid];
          if (!name) console.warn(`[MISSING] No name for ability_id: ${uuid}`);
          return name;
        })
        .filter(Boolean);

      // 🔍 Find operation creation entry
      const opToolEntry = Object.entries(traj).find(
        ([k, v]) => k.startsWith('tool_name_') && v === 'create_operation'
      );

      if (opToolEntry) {
        const opIdx = opToolEntry[0].split('_')[2];
        let opArgs = traj[`tool_args_${opIdx}`];

        try {
          if (typeof opArgs === 'string') opArgs = JSON.parse(opArgs);
        } catch {
          console.warn('[WARN] Failed to parse operation tool_args:', opArgs);
          opArgs = null;
        }

        if (opArgs?.operation_name) {
          parsedOperationLine.value = {
            name: opArgs.operation_name,
            adversaryName: opArgs.adversary_name || 'unknown'
          };
          console.debug('[DEBUG] Parsed operation args name:', opArgs.operation_name);
        }
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
function getMatchingSentenceKeys(matchFn) {
  const keys = [];
  thoughts.value.forEach((thought, tIdx) => {
    const sentences = splitSentences(thought);
    sentences.forEach((s, sIdx) => {
      if (matchFn(s)) keys.push(`${tIdx}-${sIdx}`);
    });
  });
  return keys;
}

const abilitySentenceKeys = computed(() =>
  getMatchingSentenceKeys((s) =>
    (s.includes('create') || s.includes('created') || s.includes('collected')) &&
    (s.includes('ability') || s.includes('abilities')) &&
    !s.includes('adversary')
  )
);

const adversarySentenceKeys = computed(() =>
  getMatchingSentenceKeys((s) =>
    (s.toLowerCase().includes('create') || s.toLowerCase().includes('created')) &&
    s.toLowerCase().includes('adversary')
  )
);

const operationSentenceKeys = computed(() =>
  getMatchingSentenceKeys((s) =>
    (s.toLowerCase().includes('create') || s.toLowerCase().includes('created')) &&
    s.toLowerCase().includes('operation')
  )
);
function assignInjectLocations() {
  const used = new Set();
  const injects = {};

  function place(label, keys) {
    for (let i = keys.length - 1; i >= 0; i--) {
      const [t, sOrig] = keys[i].split('-').map(Number);
      let s = sOrig;
      let slot = `${t}-${s}`;
      while (used.has(slot)) {
        slot = `${t}-${++s}`;
      }

      used.add(slot);
      injects[label] = new Set([slot]);
      return;
    }
  }

  place('ability', abilitySentenceKeys.value);
  place('adversary', adversarySentenceKeys.value);
  place('operation', operationSentenceKeys.value);

  return injects;
}

const resolvedInjects = computed(assignInjectLocations);

const lastAbilitySentenceKeys = computed(() => (resolvedInjects.value?.ability ?? new Set()));
const lastAdversarySentenceKeys = computed(() => (resolvedInjects.value?.adversary ?? new Set()));
const lastOperationSentenceKeys = computed(() => (resolvedInjects.value?.operation ?? new Set()));



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
    }, 2000)
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