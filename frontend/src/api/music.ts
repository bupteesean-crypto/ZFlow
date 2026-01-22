import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type MusicItem = {
  id: string;
  title: string;
  url: string;
  duration_sec?: number;
  cover_style?: string;
  source?: string;
  prompt?: string;
};

export async function fetchMusicLibrary(projectId: string): Promise<MusicItem[]> {
  const { data } = await request.get<ApiResponse<{ list: MusicItem[] }>>("/music/library", {
    params: { project_id: projectId },
  });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load music library");
  }
  return data.data.list || [];
}

export async function generateMusic(payload: { project_id: string; prompt: string }): Promise<MusicItem> {
  const { data } = await request.post<ApiResponse<{ music: MusicItem }>>("/music/generate", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to generate music");
  }
  return data.data.music;
}

export async function uploadMusic(projectId: string, file: File): Promise<MusicItem> {
  const form = new FormData();
  form.append("project_id", projectId);
  form.append("file", file);
  const { data } = await request.post<ApiResponse<{ music: MusicItem }>>("/music/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to upload music");
  }
  return data.data.music;
}

export async function applyStoryboardMusic(
  packageId: string,
  shotId: string,
  payload: { music_id: string; volume: number }
): Promise<void> {
  const { data } = await request.post<ApiResponse<{ binding: any }>>(
    `/music/storyboard/${packageId}/${shotId}/apply`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to apply music");
  }
}
