import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type ExportTask = {
  id: string;
  project_id: string;
  status: string;
  progress: number;
  export_config?: Record<string, unknown>;
  estimated_minutes?: number;
  file_id?: string;
  created_at?: string;
  updated_at?: string;
};

export type ExportFile = {
  id: string;
  project_id: string;
  task_id: string;
  format?: string;
  resolution?: string;
  aspect_ratio?: string;
  url?: string;
  created_at?: string;
};

export async function createExportTask(
  projectId: string,
  payload: {
    resolution?: string;
    format?: string;
    aspect_ratio?: string;
    subtitle_enabled?: boolean;
    subtitle_burn_in?: boolean;
    subtitle_style?: Record<string, unknown>;
    cover_mode?: string;
  }
): Promise<{ export_task_id: string; estimated_minutes: number }> {
  const { data } = await request.post<ApiResponse<{ export_task_id: string; estimated_minutes: number }>>(
    `/projects/${projectId}/export`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to create export task");
  }
  return data.data;
}

export async function fetchExportTask(taskId: string): Promise<ExportTask> {
  const { data } = await request.get<ApiResponse<ExportTask>>(`/export-tasks/${taskId}`);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load export task");
  }
  return data.data;
}

export async function fetchExportFiles(projectId: string): Promise<ExportFile[]> {
  const { data } = await request.get<ApiResponse<{ list: ExportFile[] }>>(
    `/projects/${projectId}/export-files`
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load export files");
  }
  return data.data.list || [];
}

export async function fetchExportDownloadUrl(fileId: string): Promise<string> {
  const { data } = await request.get<ApiResponse<{ url: string }>>(`/export-files/${fileId}/download-url`);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load download url");
  }
  return data.data.url;
}
