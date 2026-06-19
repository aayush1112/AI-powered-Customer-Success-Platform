export type UserRole = "ADMIN" | "MANAGER" | "VIEWER"

export interface UserResponse {
  id: string
  first_name: string
  last_name: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface UserListParams {
  page?: number
  page_size?: number
  search?: string
  role?: UserRole
  is_active?: boolean
  sort_by?: string
  sort_order?: "asc" | "desc"
}

export interface UserUpdateRequest {
  role?: UserRole
  is_active?: boolean
}

export interface PaginatedUsersResponse {
  items: UserResponse[]
  total: number
  page: number
  page_size: number
  pages: number
}
