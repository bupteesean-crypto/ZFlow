<template>
  <section>
    <h2>Dashboard</h2>
    <AsyncState
      :loading="loading"
      :error="error"
      :empty="isEmpty"
      empty-title="暂无数据"
      empty-text="健康检查暂时没有返回结果。"
      @retry="loadHealth"
    >
      <pre>{{ formattedHealth }}</pre>
    </AsyncState>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchHealth } from "../../api/health";
import AsyncState from "../../components/common/AsyncState.vue";

const health = ref<unknown>(null);
const error = ref<string | null>(null);
const loading = ref(true);

const formattedHealth = computed(() => JSON.stringify(health.value, null, 2));
const isEmpty = computed(() => !loading.value && !error.value && !health.value);

const loadHealth = async () => {
  loading.value = true;
  error.value = null;
  try {
    health.value = await fetchHealth();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await loadHealth();
});
</script>
