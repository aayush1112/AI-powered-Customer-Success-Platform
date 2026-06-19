import { baseApi } from "./baseApi";
import type { PaginatedResponse } from "@/features/customers/types";
import type {
  CustomerTimelineResponse,
  InteractionCreate,
  InteractionCreateResponse,
  InteractionListParams,
  InteractionResponse,
  InteractionUpdate,
  InteractionUpdateResponse,
} from "@/features/interactions/types";

export const interactionsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getInteractions: builder.query<
      PaginatedResponse<InteractionResponse>,
      InteractionListParams
    >({
      query: (params) => {
        const qs = new URLSearchParams();
        if (params.page) qs.set("page", String(params.page));
        if (params.page_size) qs.set("page_size", String(params.page_size));
        if (params.search) qs.set("search", params.search);
        if (params.customer_id) qs.set("customer_id", params.customer_id);
        if (params.interaction_type)
          qs.set("interaction_type", params.interaction_type);
        if (params.start_date) qs.set("start_date", params.start_date);
        if (params.end_date) qs.set("end_date", params.end_date);
        if (params.created_by) qs.set("created_by", params.created_by);
        if (params.sort_by) qs.set("sort_by", params.sort_by);
        if (params.sort_order) qs.set("sort_order", params.sort_order);
        return `/interactions?${qs.toString()}`;
      },
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({
                type: "Interaction" as const,
                id,
              })),
              { type: "Interaction" as const, id: "LIST" },
            ]
          : [{ type: "Interaction" as const, id: "LIST" }],
    }),

    getInteraction: builder.query<InteractionResponse, string>({
      query: (id) => `/interactions/${id}`,
      providesTags: (_result, _error, id) => [
        { type: "Interaction" as const, id },
      ],
    }),

    createInteraction: builder.mutation<
      InteractionCreateResponse,
      InteractionCreate
    >({
      query: (body) => ({ url: "/interactions", method: "POST", body }),
      invalidatesTags: [{ type: "Interaction", id: "LIST" }],
    }),

    updateInteraction: builder.mutation<
      InteractionUpdateResponse,
      { id: string; data: InteractionUpdate }
    >({
      query: ({ id, data }) => ({
        url: `/interactions/${id}`,
        method: "PUT",
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Interaction" as const, id },
        { type: "Interaction" as const, id: "LIST" },
      ],
    }),

    getCustomerTimeline: builder.query<CustomerTimelineResponse, string>({
      query: (customerId) => `/customers/${customerId}/timeline`,
      providesTags: (_result, _error, customerId) => [
        { type: "Interaction" as const, id: `timeline-${customerId}` },
        { type: "Customer" as const, id: customerId },
      ],
    }),
  }),
});

export const {
  useGetInteractionsQuery,
  useGetInteractionQuery,
  useCreateInteractionMutation,
  useUpdateInteractionMutation,
  useGetCustomerTimelineQuery,
} = interactionsApi;
