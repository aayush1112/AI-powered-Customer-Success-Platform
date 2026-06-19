export type InteractionType = "MEETING" | "CALL" | "EMAIL" | "QBR";

export interface InteractionCustomer {
  id: string;
  company_name: string;
}

export interface InteractionCreatedBy {
  id: string;
  first_name: string;
  last_name: string;
}

export interface InteractionResponse {
  id: string;
  customer_id: string;
  title: string;
  interaction_type: InteractionType;
  meeting_date: string;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  customer: InteractionCustomer;
  created_by_user: InteractionCreatedBy | null;
}

export interface InteractionCreate {
  customer_id: string;
  title: string;
  interaction_type: InteractionType;
  meeting_date: string;
  notes: string;
}

export interface InteractionUpdate {
  title?: string;
  interaction_type?: InteractionType;
  meeting_date?: string;
  notes?: string;
}

export interface InteractionFormData {
  customer_id: string;
  title: string;
  interaction_type: InteractionType;
  meeting_date: string;
  notes: string;
}

export interface InteractionCreateResponse {
  success: boolean;
  data: InteractionResponse;
}

export interface InteractionUpdateResponse {
  success: boolean;
  data: InteractionResponse;
}

export interface InteractionListParams {
  page?: number;
  page_size?: number;
  search?: string;
  customer_id?: string;
  interaction_type?: InteractionType;
  start_date?: string;
  end_date?: string;
  created_by?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface CustomerTimelineResponse {
  customer_id: string;
  company_name: string;
  interactions: InteractionResponse[];
  total: number;
}
