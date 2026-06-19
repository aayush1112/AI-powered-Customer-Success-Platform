import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError } from "@reduxjs/toolkit/query";
import type { RootState } from "@/store/store";
import { setCredentials, clearCredentials } from "@/store/slices/authSlice";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const baseQuery = fetchBaseQuery({
  baseUrl: `${API_BASE_URL}/api/v1`,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.accessToken;
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return headers;
  },
});

const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
  args,
  api,
  extraOptions
) => {
  let result = await baseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    const refreshResult = await baseQuery(
      { url: "/auth/refresh", method: "POST", credentials: "include" },
      api,
      extraOptions
    );

    if (refreshResult.data) {
      const newToken = (refreshResult.data as { access_token: string }).access_token;
      const user = (api.getState() as RootState).auth.user;
      if (user) {
        api.dispatch(setCredentials({ user, accessToken: newToken }));
      }
      result = await baseQuery(args, api, extraOptions);
    } else {
      api.dispatch(clearCredentials());
    }
  }
  return result;
};

export const baseApi = createApi({
  reducerPath: "api",
  baseQuery: baseQueryWithReauth,
  tagTypes: ["Auth", "Customer", "Interaction", "Dashboard", "Insight", "User"],
  endpoints: () => ({}),
  keepUnusedDataFor: 60,
  refetchOnMountOrArgChange: 30,
});
