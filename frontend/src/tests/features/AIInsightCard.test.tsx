import { render, screen } from "@testing-library/react";
import { AIInsightCard } from "@/features/insights/components/AIInsightCard";

const mockInsight = {
  id: "00000000-0000-0000-0000-000000000020",
  interaction_id: "00000000-0000-0000-0000-000000000001",
  summary: "Customer is satisfied with the platform and keen to expand.",
  sentiment: "POSITIVE" as const,
  action_items: ["Send renewal documents", "Schedule follow-up call"],
  risks: ["Minor churn risk if performance degrades"],
  generated_at: "2026-06-18T12:00:00Z",
};

describe("AIInsightCard", () => {
  it("renders the summary text", () => {
    render(<AIInsightCard insight={mockInsight} />);
    expect(screen.getByText(mockInsight.summary)).toBeInTheDocument();
  });

  it("renders the sentiment badge", () => {
    render(<AIInsightCard insight={mockInsight} />);
    expect(screen.getByText(/positive/i)).toBeInTheDocument();
  });

  it("renders all action items", () => {
    render(<AIInsightCard insight={mockInsight} />);
    for (const item of mockInsight.action_items) {
      expect(screen.getByText(item)).toBeInTheDocument();
    }
  });

  it("renders risks list", () => {
    render(<AIInsightCard insight={mockInsight} />);
    for (const risk of mockInsight.risks) {
      expect(screen.getByText(risk)).toBeInTheDocument();
    }
  });

  it("renders negative sentiment correctly", () => {
    const neg = { ...mockInsight, sentiment: "NEGATIVE" as const };
    render(<AIInsightCard insight={neg} />);
    expect(screen.getByText(/negative/i)).toBeInTheDocument();
  });

  it("renders neutral sentiment correctly", () => {
    const neu = { ...mockInsight, sentiment: "NEUTRAL" as const };
    render(<AIInsightCard insight={neu} />);
    expect(screen.getByText(/neutral/i)).toBeInTheDocument();
  });

  it("renders empty action items without crashing", () => {
    const noActions = { ...mockInsight, action_items: [] };
    render(<AIInsightCard insight={noActions} />);
    expect(screen.getByText(mockInsight.summary)).toBeInTheDocument();
  });
});
