import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type AttachmentItem = {
  id: string;
  filename: string;
  content_type: string;
  size: number;
  category: string;
  url: string;
  label?: string;
  bind_type?: string;
  tags?: string[];
  parsed_text?: string;
  parse_status?: string;
  image_meta?: {
    width?: number;
    height?: number;
  };
  created_at?: string;
};

export async function uploadAttachment(
  projectId: string,
  file: File,
  label?: string,
  bindType?: string,
  tags?: string[],
  onProgress?: (percent: number) => void
): Promise<AttachmentItem> {
  const form = new FormData();
  form.append("file", file);
  if (label) {
    form.append("label", label);
  }
  if (bindType) {
    form.append("bind_type", bindType);
  }
  if (tags && tags.length) {
    form.append("tags", tags.join(","));
  }
  const { data } = await request.post<ApiResponse<{ attachment: AttachmentItem }>>(
    `/projects/${projectId}/attachments`,
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: event => {
        if (!event.total) return;
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress?.(percent);
      },
    }
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to upload attachment");
  }
  return data.data.attachment;
}

export async function fetchAttachments(projectId: string): Promise<AttachmentItem[]> {
  const { data } = await request.get<ApiResponse<{ list: AttachmentItem[] }>>(
    `/projects/${projectId}/attachments`
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load attachments");
  }
  return data.data.list || [];
}

export async function updateAttachment(
  projectId: string,
  attachmentId: string,
  payload: { label?: string; bind_type?: string; tags?: string[] }
): Promise<AttachmentItem> {
  const { data } = await request.patch<ApiResponse<{ attachment: AttachmentItem }>>(
    `/projects/${projectId}/attachments/${attachmentId}`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update attachment");
  }
  return data.data.attachment;
}
