import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type RegenerateImageResponse = {
  image: Record<string, any>;
  material_package_id: string;
};

export async function regenerateImage(
  imageId: string,
  prompt: string,
  promptSource?: string,
  size?: string
): Promise<RegenerateImageResponse> {
  const payload: { prompt: string; prompt_source?: string; size?: string } = { prompt };
  if (promptSource) {
    payload.prompt_source = promptSource;
  }
  if (size) {
    payload.size = size;
  }
  const { data } = await request.post<ApiResponse<RegenerateImageResponse>>(
    `/images/${imageId}/regenerate`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to regenerate image");
  }
  return data.data;
}

export type RewritePromptResponse = {
  rewritten_prompt: string;
  source_image_id: string;
};

export async function rewriteImagePrompt(imageId: string, feedback: string): Promise<RewritePromptResponse> {
  const payload = { feedback };
  const { data } = await request.post<ApiResponse<RewritePromptResponse>>(
    `/images/${imageId}/feedback`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to rewrite prompt");
  }
  return data.data;
}

export type AdoptImageResponse = {
  image_id: string;
  material_package_id: string;
};

export async function adoptImage(imageId: string): Promise<AdoptImageResponse> {
  const { data } = await request.post<ApiResponse<AdoptImageResponse>>(`/images/${imageId}/adopt`);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to adopt image");
  }
  return data.data;
}
