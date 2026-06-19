import { render, screen } from "@testing-library/react";
import { SentimentBadge } from "@/features/insights/components/SentimentBadge";

describe("SentimentBadge", () => {
  it("renders 'Positive' for POSITIVE sentiment", () => {
    render(<SentimentBadge sentiment="POSITIVE" />);
    expect(screen.getByText("Positive")).toBeInTheDocument();
  });

  it("renders 'Neutral' for NEUTRAL sentiment", () => {
    render(<SentimentBadge sentiment="NEUTRAL" />);
    expect(screen.getByText("Neutral")).toBeInTheDocument();
  });

  it("renders 'Negative' for NEGATIVE sentiment", () => {
    render(<SentimentBadge sentiment="NEGATIVE" />);
    expect(screen.getByText("Negative")).toBeInTheDocument();
  });

  it("applies green colour classes for POSITIVE", () => {
    render(<SentimentBadge sentiment="POSITIVE" />);
    const badge = screen.getByText("Positive");
    expect(badge).toHaveClass("text-green-800");
  });

  it("applies red colour classes for NEGATIVE", () => {
    render(<SentimentBadge sentiment="NEGATIVE" />);
    const badge = screen.getByText("Negative");
    expect(badge).toHaveClass("text-red-800");
  });

  it("applies slate colour classes for NEUTRAL", () => {
    render(<SentimentBadge sentiment="NEUTRAL" />);
    const badge = screen.getByText("Neutral");
    expect(badge).toHaveClass("text-slate-700");
  });
});
