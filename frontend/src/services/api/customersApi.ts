import { baseApi } from "./baseApi";
import type {
  CustomerCreate,
  CustomerCreateResponse,
  CustomerListParams,
  CustomerResponse,
  CustomerUpdate,
  CustomerUpdateResponse,
  PaginatedResponse,
} from "@/features/customers/types";

export const customersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getCustomers: builder.query<
      PaginatedResponse<CustomerResponse>,
      CustomerListParams
    >({
      query: (params) => {
        const qs = new URLSearchParams();
        if (params.page) qs.set("page", String(params.page));
        if (params.page_size) qs.set("page_size", String(params.page_size));
        if (params.search) qs.set("search", params.search);
        if (params.status) qs.set("status", params.status);
        if (params.industry) qs.set("industry", params.industry);
        if (params.sort_by) qs.set("sort_by", params.sort_by);
        if (params.sort_order) qs.set("sort_order", params.sort_order);
        return `/customers?${qs.toString()}`;
      },
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({
                type: "Customer" as const,
                id,
              })),
              { type: "Customer" as const, id: "LIST" },
            ]
          : [{ type: "Customer" as const, id: "LIST" }],
    }),

    getCustomer: builder.query<CustomerResponse, string>({
      query: (id) => `/customers/${id}`,
      providesTags: (_result, _error, id) => [{ type: "Customer" as const, id }],
    }),

    createCustomer: builder.mutation<CustomerCreateResponse, CustomerCreate>({
      query: (body) => ({ url: "/customers", method: "POST", body }),
      invalidatesTags: [{ type: "Customer", id: "LIST" }],
    }),

    updateCustomer: builder.mutation<
      CustomerUpdateResponse,
      { id: string; data: CustomerUpdate }
    >({
      query: ({ id, data }) => ({
        url: `/customers/${id}`,
        method: "PUT",
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Customer" as const, id },
        { type: "Customer" as const, id: "LIST" },
      ],
    }),

    deleteCustomer: builder.mutation<void, string>({
      query: (id) => ({ url: `/customers/${id}`, method: "DELETE" }),
      invalidatesTags: (_result, _error, id) => [
        { type: "Customer" as const, id },
        { type: "Customer" as const, id: "LIST" },
      ],
    }),
  }),
});

export const {
  useGetCustomersQuery,
  useGetCustomerQuery,
  useCreateCustomerMutation,
  useUpdateCustomerMutation,
  useDeleteCustomerMutation,
} = customersApi;
