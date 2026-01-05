import request from "./request";

export async function fetchTasks(): Promise<unknown> {
  const { data } = await request.get("/tasks");
  return data;
}

export async function fetchTask(taskId: string): Promise<unknown> {
  const { data } = await request.get(`/tasks/${taskId}`);
  return data;
}

export async function createTask(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await request.post("/tasks", payload);
  return data;
}
