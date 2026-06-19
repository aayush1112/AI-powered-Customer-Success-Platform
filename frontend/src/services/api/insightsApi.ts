import { baseApi } from "./baseApi";
import type {
  AIInsightGenerateResponse,
  AIInsightResponse,
} from "@/features/insights/types";

export const insightsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getInsight: builder.query<AIInsightResponse, string>({
      query: (interactionId) => `/insights/${interactionId}`,
      providesTags: (_result, _error, interactionId) => [
        { type: "Insight" as const, id: interactionId },
      ],
    }),

    generateInsight: builder.mutation<AIInsightGenerateResponse, string>({
      query: (interactionId) => ({
        url: `/insights/generate/${interactionId}`,
        method: "POST",
      }),
      invalidatesTags: (_result, _error, interactionId) => [
        { type: "Insight" as const, id: interactionId },
      ],
    }),

    regenerateInsight: builder.mutation<AIInsightGenerateResponse, string>({
      query: (interactionId) => ({
        url: `/insights/regenerate/${interactionId}`,
        method: "POST",
      }),
      invalidatesTags: (_result, _error, interactionId) => [
        { type: "Insight" as const, id: interactionId },
      ],
    }),
  }),
});

export const {
  useGetInsightQuery,
  useGenerateInsightMutation,
  useRegenerateInsightMutation,
} = insightsApi;
