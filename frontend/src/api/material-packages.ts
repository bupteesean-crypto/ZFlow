import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type MaterialPackage = {
  id: string;
  project_id: string;
  package_name: string;
  status: string;
  is_active?: boolean;
  summary?: string | null;
  materials?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type MaterialPackageListResponse = {
  list: MaterialPackage[];
  total: number;
};

export async function fetchMaterialPackages(projectId: string): Promise<MaterialPackageListResponse> {
  const { data } = await request.get<ApiResponse<MaterialPackageListResponse>>(
    `/projects/${projectId}/material-packages`
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load material packages");
  }
  return data.data;
}

export async function fetchMaterialPackage(packageId: string): Promise<MaterialPackage> {
  const { data } = await request.get<ApiResponse<MaterialPackage>>(
    `/material-packages/${packageId}`
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load material package");
  }
  return data.data;
}

export async function submitMaterialPackageFeedback(
  packageId: string,
  feedback: string,
  imageModelId?: string
): Promise<MaterialPackage> {
  const payload: { feedback: string; image_model_id?: string } = { feedback };
  if (imageModelId) {
    payload.image_model_id = imageModelId;
  }
  const { data } = await request.post<ApiResponse<MaterialPackage>>(
    `/material-packages/${packageId}/feedback`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to submit material package feedback");
  }
  return data.data;
}

export async function generateStoryboardImages(
  packageId: string,
  force = false,
  modelId?: string
): Promise<{ generated: unknown[]; material_package_id: string }> {
  const payload: { force: boolean; model_id?: string } = { force };
  if (modelId) {
    payload.model_id = modelId;
  }
  const { data } = await request.post<ApiResponse<{ generated: unknown[]; material_package_id: string }>>(
    `/material-packages/${packageId}/storyboard-images`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to generate storyboard images");
  }
  return data.data;
}

export async function generateStoryboardVideos(
  packageId: string,
  payload: {
    shot_id?: string;
    prompt?: string;
    feedback?: string;
    force?: boolean;
    model?: string;
    model_id?: string;
    size?: string;
  } = {}
): Promise<{ generated: unknown[]; skipped?: unknown[]; material_package_id: string }> {
  const { data } = await request.post<
    ApiResponse<{ generated: unknown[]; skipped?: unknown[]; material_package_id: string }>
  >(`/material-packages/${packageId}/storyboard-videos`, payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to generate storyboard videos");
  }
  return data.data;
}

export async function fetchStoryboardVideoTask(
  packageId: string,
  taskId: string
): Promise<{ task: Record<string, unknown>; video: Record<string, unknown>; material_package_id: string }> {
  const { data } = await request.get<
    ApiResponse<{ task: Record<string, unknown>; video: Record<string, unknown>; material_package_id: string }>
  >(`/material-packages/${packageId}/storyboard-videos/${taskId}`);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to fetch storyboard video task");
  }
  return data.data;
}

export async function updateMaterialPackage(
  packageId: string,
  payload: Partial<MaterialPackage>
): Promise<MaterialPackage> {
  const { data } = await request.put<ApiResponse<MaterialPackage>>(
    `/material-packages/${packageId}`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update material package");
  }
  return data.data;
}
