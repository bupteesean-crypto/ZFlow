import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type GenerationTask = {
  id: string;
  project_id: string;
  material_package_id?: string;
  status: string;
  progress: number;
  updated_at?: string;
};

export type GenerationProgressResponse = {
  list: GenerationTask[];
};

export async function startGeneration(
  projectId: string,
  prompt?: string,
  mode?: string
): Promise<GenerationTask> {
  const payload: { project_id: string; prompt?: string; mode?: string } = { project_id: projectId };
  if (prompt) {
    payload.prompt = prompt;
  }
  if (mode) {
    payload.mode = mode;
  }
  const { data } = await request.post<ApiResponse<GenerationTask>>("/generation/start", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to start generation");
  }
  return data.data;
}

export async function fetchGenerationProgress(
  projectId: string
): Promise<GenerationProgressResponse> {
  const { data } = await request.get<ApiResponse<GenerationProgressResponse>>(
    `/generation/progress/${projectId}`
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load generation progress");
  }
  return data.data;
}
