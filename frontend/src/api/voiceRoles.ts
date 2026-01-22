import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type VoiceRole = {
  id: string;
  project_id: string;
  name: string;
  voice_id?: string | null;
  emotion?: string | null;
  volume?: number;
  speed?: number;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
};

export async function fetchVoiceRoles(projectId: string): Promise<VoiceRole[]> {
  const { data } = await request.get<ApiResponse<{ list: VoiceRole[] }>>("/voice-roles", {
    params: { project_id: projectId },
  });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load voice roles");
  }
  return data.data.list || [];
}

export async function createVoiceRole(payload: {
  project_id: string;
  name: string;
  voice_id?: string;
  emotion?: string;
  volume?: number;
  speed?: number;
}): Promise<VoiceRole> {
  const { data } = await request.post<ApiResponse<{ role: VoiceRole }>>("/voice-roles", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to create voice role");
  }
  return data.data.role;
}

export async function updateVoiceRole(
  roleId: string,
  payload: {
    name?: string;
    voice_id?: string;
    emotion?: string;
    volume?: number;
    speed?: number;
  }
): Promise<VoiceRole> {
  const { data } = await request.put<ApiResponse<{ role: VoiceRole }>>(`/voice-roles/${roleId}`, payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update voice role");
  }
  return data.data.role;
}
