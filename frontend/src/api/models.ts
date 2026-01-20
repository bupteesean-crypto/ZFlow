import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type ModelOption = {
  id: string;
  type: "image" | "video";
  provider: string;
  model: string;
  label: string;
  enabled: boolean;
  is_default?: boolean;
  disabled_reason?: string | null;
};

export async function fetchModels(type?: "image" | "video"): Promise<ModelOption[]> {
  const params = type ? { type } : {};
  const { data } = await request.get<ApiResponse<{ list: ModelOption[] }>>("/models", { params });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load models");
  }
  return data.data.list || [];
}
