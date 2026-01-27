import request from "./request";

type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type LoginResponse = {
  user: {
    id: string;
    uid?: string;
    username: string;
    display_name?: string | null;
    account_type: "personal" | "company";
    roles?: string[];
    company_id?: string | null;
    is_platform_admin?: boolean;
    avatar_url?: string | null;
    llm_api_base?: string;
    llm_configured?: boolean;
  };
  session_token: string;
  refresh_token: string;
  current_space: {
    type: "personal" | "company";
    space_id?: string | null;
    space_name?: string | null;
  };
  authenticated: boolean;
};

export async function login(payload: {
  username: string;
  password: string;
}): Promise<LoginResponse> {
  const { data } = await request.post<ApiResponse<LoginResponse>>("/auth/login", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Login failed");
  }
  return data.data;
}

export type UserAccount = {
  id: string;
  uid: string;
  username: string;
  display_name?: string | null;
  avatar_url?: string | null;
  account_type: "personal" | "company";
  roles: string[];
  company_id?: string | null;
  is_platform_admin?: boolean;
  created_at?: string;
  updated_at?: string;
};

export async function fetchUsers(): Promise<{ list: UserAccount[]; total: number }> {
  const { data } = await request.get<ApiResponse<{ list: UserAccount[]; total: number }>>("/auth/users");
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load users");
  }
  return data.data;
}

export async function createUser(payload: {
  username: string;
  password: string;
  account_type?: "personal" | "company";
  roles?: string[];
  company_invite_code?: string;
  create_company_name?: string;
}): Promise<UserAccount> {
  const { data } = await request.post<ApiResponse<UserAccount>>("/auth/users", payload);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to create user");
  }
  return data.data;
}

export async function updateUserPassword(userId: string, password: string): Promise<UserAccount> {
  const { data } = await request.put<ApiResponse<UserAccount>>(`/auth/users/${userId}/password`, { password });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to update password");
  }
  return data.data;
}

export type Company = {
  id: string;
  name: string;
  invite_code: string;
  created_at?: string;
  updated_at?: string;
};

export async function fetchCompanies(): Promise<{ list: Company[]; total: number }> {
  const { data } = await request.get<ApiResponse<{ list: Company[]; total: number }>>("/auth/companies");
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to load companies");
  }
  return data.data;
}

export async function createCompany(name: string): Promise<Company> {
  const { data } = await request.post<ApiResponse<Company>>("/auth/companies", { name });
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to create company");
  }
  return data.data;
}

export async function resetCompanyInvite(companyId: string): Promise<Company> {
  const { data } = await request.put<ApiResponse<Company>>(`/auth/companies/${companyId}/invite`);
  if (data.code !== 0) {
    throw new Error(data.message || "Failed to reset invite code");
  }
  return data.data;
}
