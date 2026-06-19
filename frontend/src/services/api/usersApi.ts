import { baseApi } from "./baseApi"
import type {
  PaginatedUsersResponse,
  UserListParams,
  UserResponse,
  UserUpdateRequest,
} from "@/features/admin/types"

export const usersApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getUsers: build.query<PaginatedUsersResponse, UserListParams>({
      query: (params) => ({ url: "/users", params }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({ type: "User" as const, id })),
              { type: "User" as const, id: "LIST" },
            ]
          : [{ type: "User" as const, id: "LIST" }],
    }),

    getUser: build.query<UserResponse, string>({
      query: (id) => `/users/${id}`,
      providesTags: (_, __, id) => [{ type: "User" as const, id }],
    }),

    updateUser: build.mutation<UserResponse, { id: string; data: UserUpdateRequest }>({
      query: ({ id, data }) => ({ url: `/users/${id}`, method: "PUT", body: data }),
      invalidatesTags: (_, __, { id }) => [
        { type: "User" as const, id },
        { type: "User" as const, id: "LIST" },
      ],
    }),
  }),
})

export const { useGetUsersQuery, useGetUserQuery, useUpdateUserMutation } = usersApi
