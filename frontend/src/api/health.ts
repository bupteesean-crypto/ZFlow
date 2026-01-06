import axios from "axios";

export async function fetchHealth(): Promise<unknown> {
  const { data } = await axios.get("http://localhost:8000/health");
  return data;
}
