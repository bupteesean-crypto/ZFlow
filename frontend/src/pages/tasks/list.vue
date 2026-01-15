<template>
  <section>
    <h2>Tasks</h2>
    <form @submit.prevent="handleCreate">
      <label>
        Prompt
        <input v-model="prompt" type="text" placeholder="Optional prompt" />
      </label>
      <button type="submit" :disabled="creating">Create task</button>
    </form>

    <AsyncState
      :loading="loading"
      :error="error"
      :empty="tasks.length === 0"
      empty-title="暂无任务"
      empty-text="还没有任务，创建一个试试。"
      @retry="loadTasks(true)"
    >
      <table v-if="tasks.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Pipeline</th>
            <th>Status</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>{{ task.id }}</td>
            <td>{{ task.pipeline ?? "-" }}</td>
            <td>{{ task.status }}</td>
            <td>{{ task.created_at ?? "-" }}</td>
            <td>
              <RouterLink v-if="task.id" :to="`/tasks/${task.id}`">View</RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </AsyncState>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { createTask, fetchTasks } from "../../api/tasks";
import AsyncState from "../../components/common/AsyncState.vue";

type Task = {
  id?: string | number;
  status?: string;
  created_at?: string;
  pipeline?: string;
  input?: unknown;
  output?: unknown;
};

const tasks = ref<Task[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);
const creating = ref(false);
const prompt = ref("");

const loadTasks = async (showSpinner: boolean) => {
  if (showSpinner) {
    loading.value = true;
  }
  error.value = null;
  try {
    const data = await fetchTasks();
    tasks.value = Array.isArray(data) ? (data as Task[]) : [];
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    if (showSpinner) {
      loading.value = false;
    }
  }
};

const handleCreate = async () => {
  creating.value = true;
  error.value = null;
  try {
    const payload = prompt.value ? { prompt: prompt.value } : {};
    await createTask(payload);
    prompt.value = "";
    await loadTasks(true);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    creating.value = false;
  }
};

let poller: number | undefined;

onMounted(async () => {
  await loadTasks(true);
  poller = window.setInterval(() => loadTasks(false), 2500);
});

onUnmounted(() => {
  if (poller) {
    window.clearInterval(poller);
  }
});
</script>
