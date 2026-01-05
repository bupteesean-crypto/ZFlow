import request from "./request";

export async function fetchHealth(): Promise<unknown> {
  const { data } = await request.get("/health");
  return data;
}
