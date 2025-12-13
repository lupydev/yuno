import type { UserData } from "../types/user";
export interface LoginResponse {
  token: string;
  refreshToken: string;
  userData: UserData;
}