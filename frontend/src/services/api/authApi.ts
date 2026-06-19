import { baseApi } from "./baseApi";
import type {
  AccessTokenResponse,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
  UserResponse,
} from "@/features/auth/types";

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    register: builder.mutation<RegisterResponse, RegisterRequest>({
      query: (body) => ({
        url: "/auth/register",
        method: "POST",
        body,
      }),
    }),

    login: builder.mutation<TokenResponse, LoginRequest>({
      query: (body) => ({
        url: "/auth/login",
        method: "POST",
        body,
      }),
    }),

    logout: builder.mutation<MessageResponse, void>({
      query: () => ({
        url: "/auth/logout",
        method: "POST",
      }),
      invalidatesTags: ["Auth"],
    }),

    refresh: builder.mutation<AccessTokenResponse, void>({
      query: () => ({
        url: "/auth/refresh",
        method: "POST",
      }),
    }),

    me: builder.query<UserResponse, void>({
      query: () => "/auth/me",
      providesTags: ["Auth"],
    }),
  }),
  overrideExisting: false,
});

export const {
  useRegisterMutation,
  useLoginMutation,
  useLogoutMutation,
  useRefreshMutation,
  useMeQuery,
} = authApi;
