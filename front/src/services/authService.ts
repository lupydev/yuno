import apiBackClient from "./apiBackClient";

export const login = async (email: string, password: string) => {
  const response = await apiBackClient.post("/auth/login", { email, password });
  return response.data;
};

export const logout = async () => {
  await apiBackClient.post("/auth/logout");
};
