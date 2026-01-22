import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type TextCandidateResponse<T> = {
  candidate: T;
  material_package_id: string;
};

export async function submitArtStyleFeedback(materialPackageId: string, feedback: string) {
  const payload = { material_package_id: materialPackageId, feedback };
  const { data } = await request.post<ApiResponse<TextCandidateResponse<Record<string, any>>>>(
    "/text/art-style/feedback",
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to submit art style feedback");
  }
  return data.data;
}

export async function submitStoryboardFeedback(
  materialPackageId: string,
  shotId: string,
  feedback: string
) {
  const payload = { material_package_id: materialPackageId, feedback };
  const { data } = await request.post<ApiResponse<TextCandidateResponse<Record<string, any>>>>(
    `/text/storyboard/${shotId}/feedback`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to submit storyboard feedback");
  }
  return data.data;
}

export async function adoptTextCandidate(
  materialPackageId: string,
  targetType: "art_style" | "storyboard_description" | "summary" | "subject" | "scene",
  candidateId: string,
  shotId?: string,
  subjectId?: string,
  sceneId?: string
) {
  const payload: Record<string, any> = {
    material_package_id: materialPackageId,
    target_type: targetType,
    candidate_id: candidateId,
  };
  if (shotId) {
    payload.shot_id = shotId;
  }
  if (subjectId) {
    payload.subject_id = subjectId;
  }
  if (sceneId) {
    payload.scene_id = sceneId;
  }
  const { data } = await request.post<ApiResponse<Record<string, any>>>("/text/adopt", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to adopt candidate");
  }
  return data.data;
}

export async function submitSummaryFeedback(materialPackageId: string, feedback: string) {
  const payload = { material_package_id: materialPackageId, feedback };
  const { data } = await request.post<ApiResponse<TextCandidateResponse<Record<string, any>>>>(
    "/text/summary/feedback",
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to submit summary feedback");
  }
  return data.data;
}

export async function submitSubjectFeedback(
  materialPackageId: string,
  subjectId: string,
  feedback: string
) {
  const payload = { material_package_id: materialPackageId, feedback };
  const { data } = await request.post<ApiResponse<TextCandidateResponse<Record<string, any>>>>(
    `/text/subjects/${subjectId}/feedback`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to submit subject feedback");
  }
  return data.data;
}

export async function submitSceneFeedback(
  materialPackageId: string,
  sceneId: string,
  feedback: string
) {
  const payload = { material_package_id: materialPackageId, feedback };
  const { data } = await request.post<ApiResponse<TextCandidateResponse<Record<string, any>>>>(
    `/text/scenes/${sceneId}/feedback`,
    payload
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to submit scene feedback");
  }
  return data.data;
}
