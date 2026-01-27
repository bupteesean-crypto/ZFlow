import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type LlmSettings = {
  api_base: string;
  has_api_key: boolean;
};

export async function fetchLlmSettings(): Promise<LlmSettings> {
  const { data } = await request.get<ApiResponse<LlmSettings>>("/users/me/llm-settings");
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load LLM settings");
  }
  return data.data;
}

export async function updateLlmSettings(payload: {
  api_base: string;
  api_key?: string;
}): Promise<LlmSettings> {
  const { data } = await request.put<ApiResponse<LlmSettings>>("/users/me/llm-settings", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update LLM settings");
  }
  return data.data;
}
