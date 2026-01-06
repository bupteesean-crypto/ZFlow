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
