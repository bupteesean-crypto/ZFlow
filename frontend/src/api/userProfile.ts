import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type UserProfile = {
  id: string;
  username: string;
  display_name: string;
  avatar_url: string;
};

export async function fetchMyProfile(): Promise<UserProfile> {
  const { data } = await request.get<ApiResponse<UserProfile>>("/users/me/profile");
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load profile");
  }
  return data.data;
}

export async function updateMyProfile(payload: {
  display_name?: string;
  avatar_url?: string;
}): Promise<UserProfile> {
  const { data } = await request.put<ApiResponse<UserProfile>>("/users/me/profile", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update profile");
  }
  return data.data;
}

export async function uploadMyAvatar(file: File): Promise<{ avatar_url: string }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await request.post<ApiResponse<{ avatar_url: string }>>("/users/me/avatar", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to upload avatar");
  }
  return data.data;
}

export async function updateUserProfileByAdmin(
  userId: string,
  payload: { display_name?: string; avatar_url?: string },
): Promise<UserProfile> {
  const { data } = await request.put<ApiResponse<UserProfile>>(`/users/${userId}/profile`, payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update user profile");
  }
  return data.data;
}

export async function uploadUserAvatarByAdmin(
  userId: string,
  file: File,
): Promise<{ avatar_url: string }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await request.post<ApiResponse<{ avatar_url: string }>>(
    `/users/${userId}/avatar`,
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to upload avatar");
  }
  return data.data;
}
