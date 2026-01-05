<template>
  <section>
    <h2>Dashboard</h2>
    <p v-if="loading">Loading...</p>
    <p v-else-if="error">Error: {{ error }}</p>
    <pre v-else>{{ formattedHealth }}</pre>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchHealth } from "../../api/health";

const health = ref<unknown>(null);
const error = ref<string | null>(null);
const loading = ref(true);

const formattedHealth = computed(() => JSON.stringify(health.value, null, 2));

onMounted(async () => {
  try {
    health.value = await fetchHealth();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    loading.value = false;
  }
});
</script>
