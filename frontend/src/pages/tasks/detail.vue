<template>
  <section>
    <h2>Task Detail</h2>
    <p v-if="loading">Loading...</p>
    <p v-else-if="error">Error: {{ error }}</p>
    <div v-else-if="task">
      <section>
        <h3>Metadata</h3>
        <table>
          <tbody>
            <tr>
              <th>ID</th>
              <td>{{ task.id }}</td>
            </tr>
            <tr>
              <th>Pipeline</th>
              <td>{{ task.pipeline ?? "-" }}</td>
            </tr>
            <tr>
              <th>Created</th>
              <td>{{ task.created_at ?? "-" }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section>
        <h3>Status</h3>
        <p>Current: {{ task.status ?? "-" }}</p>
        <ul>
          <li v-for="step in statusSteps" :key="step">
            <strong v-if="task.status === step">{{ step }}</strong>
            <span v-else>{{ step }}</span>
          </li>
        </ul>
      </section>

      <section>
        <h3>Input</h3>
        <pre>{{ formattedInput }}</pre>
      </section>

      <section>
        <h3>Output</h3>
        <pre>{{ formattedOutput }}</pre>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { fetchTask } from "../../api/tasks";

type Task = {
  id?: string | number;
  status?: string;
  created_at?: string;
  pipeline?: string;
  input?: unknown;
  output?: unknown;
};

const route = useRoute();
const task = ref<Task | null>(null);
const error = ref<string | null>(null);
const loading = ref(true);
const statusSteps = ["pending", "running", "done"];

const formatValue = (value: unknown) => {
  if (value === undefined) {
    return "";
  }
  if (value === null) {
    return "null";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
};

const formattedInput = computed(() => formatValue(task.value?.input));
const formattedOutput = computed(() => formatValue(task.value?.output));

const loadTask = async (showSpinner: boolean) => {
  const taskId = route.params.id;
  if (!taskId || Array.isArray(taskId)) {
    error.value = "Invalid task id";
    loading.value = false;
    return;
  }
  if (showSpinner) {
    loading.value = true;
  }
  error.value = null;
  try {
    const data = await fetchTask(taskId);
    task.value = data as Task;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    if (showSpinner) {
      loading.value = false;
    }
  }
};

let poller: number | undefined;

onMounted(async () => {
  await loadTask(true);
  poller = window.setInterval(() => loadTask(false), 2500);
});

watch(
  () => route.params.id,
  async () => {
    await loadTask(true);
  }
);

onUnmounted(() => {
  if (poller) {
    window.clearInterval(poller);
  }
});
</script>
