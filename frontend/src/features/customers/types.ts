export type CustomerStatus = "ACTIVE" | "AT_RISK" | "CHURNED" | "PROSPECT";

export interface CustomerResponse {
  id: string;
  company_name: string;
  industry: string | null;
  contact_name: string;
  contact_email: string;
  contact_phone: string | null;
  status: CustomerStatus;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  company_name: string;
  industry?: string | null;
  contact_name: string;
  contact_email: string;
  contact_phone?: string | null;
}

export interface CustomerUpdate {
  company_name?: string;
  industry?: string | null;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string | null;
  status?: CustomerStatus;
}

export interface CustomerFormData {
  company_name: string;
  industry?: string | null;
  contact_name: string;
  contact_email: string;
  contact_phone?: string | null;
  status?: CustomerStatus;
}

export interface CustomerCreateResponse {
  success: boolean;
  data: CustomerResponse;
}

export interface CustomerUpdateResponse {
  success: boolean;
  data: CustomerResponse;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface CustomerListParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: CustomerStatus;
  industry?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
