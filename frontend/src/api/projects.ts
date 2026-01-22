import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type Project = {
  id: string;
  name: string;
  description?: string | null;
  status: string;
  stage?: string;
  progress?: number;
  tags?: string[];
  input_config?: Record<string, any>;
  metadata?: Record<string, any>;
  updated_at?: string;
  created_at?: string;
  last_material_package_id?: string | null;
};

export type ProjectListResponse = {
  list: Project[];
  total: number;
  page: number;
  page_size: number;
};

export async function fetchProjects(page = 1, pageSize = 20): Promise<ProjectListResponse> {
  const { data } = await request.get<ApiResponse<ProjectListResponse>>("/projects", {
    params: { page, page_size: pageSize },
  });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load projects");
  }
  return data.data;
}

export async function fetchProject(projectId: string): Promise<Project> {
  const { data } = await request.get<ApiResponse<Project>>(`/projects/${projectId}`);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load project");
  }
  return data.data;
}

export async function createProject(payload: {
  name?: string;
  space_type?: "personal" | "team";
  team_space_id?: string | null;
}): Promise<Project> {
  const { data } = await request.post<ApiResponse<Project>>("/projects", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to create project");
  }
  return data.data;
}

export async function updateProject(
  projectId: string,
  payload: Partial<Project> & { input_config?: Record<string, any>; metadata?: Record<string, any> }
): Promise<Project> {
  const { data } = await request.put<ApiResponse<Project>>(`/projects/${projectId}`, payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update project");
  }
  return data.data;
}
