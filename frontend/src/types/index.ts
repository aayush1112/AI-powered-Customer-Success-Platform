export type { ApiResponse, ApiError, PaginationMeta, PaginatedResponse, QueryParams } from "./api";

export type ID = string;
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type AsyncStatus = "idle" | "loading" | "succeeded" | "failed";
