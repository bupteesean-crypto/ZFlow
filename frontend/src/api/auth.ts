import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type LoginResponse = {
  user: {
    id: string;
    username: string;
    user_type: "personal" | "team";
    avatar_url?: string | null;
  };
  session_token: string;
  refresh_token: string;
  current_space: {
    type: "personal" | "team";
    space_id?: string | null;
    space_name?: string | null;
  };
  authenticated: boolean;
};

export async function login(payload: {
  phone: string;
  code: string;
  invite_code?: string;
}): Promise<LoginResponse> {
  const { data } = await request.post<ApiResponse<LoginResponse>>("/auth/login", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Login failed");
  }
  return data.data;
}
