export type SentimentType = "POSITIVE" | "NEUTRAL" | "NEGATIVE";

export interface AIInsightResponse {
  id: string;
  interaction_id: string;
  summary: string;
  sentiment: SentimentType;
  action_items: string[];
  risks: string[];
  generated_at: string;
}

export interface AIInsightGenerateResponse {
  success: boolean;
  data: AIInsightResponse;
  is_fallback: boolean;
}
