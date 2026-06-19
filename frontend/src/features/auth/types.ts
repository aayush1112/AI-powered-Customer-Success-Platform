export type UserRole = "ADMIN" | "MANAGER" | "VIEWER";

export interface UserResponse {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  success: boolean;
  message: string;
}

export interface MessageResponse {
  success: boolean;
  message: string;
}
