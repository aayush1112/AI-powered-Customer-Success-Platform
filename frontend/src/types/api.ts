export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  errors?: ApiError[];
}

export interface ApiError {
  field?: string;
  message: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  meta: PaginationMeta;
}

export interface QueryParams {
  page?: number;
  size?: number;
  search?: string;
  sort?: string;
  order?: "asc" | "desc";
}
