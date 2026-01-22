import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type VoiceOption = {
  id: string;
  name: string;
  gender?: string;
  age_group?: string;
  locale?: string;
  description?: string;
};

export type TtsAudio = {
  id: string;
  url: string;
  duration_sec?: number;
  text?: string;
  voice_id?: string | null;
  emotion?: string | null;
  speed?: number;
  volume?: number;
  role_id?: string | null;
};

export async function fetchVoiceOptions(): Promise<VoiceOption[]> {
  const { data } = await request.get<ApiResponse<{ list: VoiceOption[] }>>("/tts/voices");
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load voices");
  }
  return data.data.list || [];
}

export async function previewTts(payload: {
  project_id: string;
  text: string;
  voice_id?: string;
  emotion?: string;
  speed?: number;
  volume?: number;
}): Promise<TtsAudio> {
  const { data } = await request.post<ApiResponse<{ audio: TtsAudio }>>("/tts/preview", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to preview TTS");
  }
  return data.data.audio;
}

export async function generateStoryboardAudio(
  packageId: string,
  shotId: string,
  payload: {
    text: string;
    voice_id?: string;
    emotion?: string;
    speed?: number;
    volume?: number;
    role_id?: string;
  }
): Promise<TtsAudio> {
  const { data } = await request.post<ApiResponse<{ audio: TtsAudio }>>(
    `/tts/storyboard/${packageId}/${shotId}`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to generate audio");
  }
  return data.data.audio;
}
