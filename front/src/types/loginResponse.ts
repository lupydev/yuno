import type { UserData } from "../types/user";

export interface LoginResponse {
  token: string;
  refresh_token: string;
  user_data: UserData;
}