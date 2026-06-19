import { render, screen } from "@testing-library/react";
import { MetricCard } from "@/features/dashboard/components/MetricCard";

describe("MetricCard", () => {
  it("renders the title", () => {
    render(<MetricCard title="Total Customers" value={42} />);
    expect(screen.getByText("Total Customers")).toBeInTheDocument();
  });

  it("renders a formatted numeric value", () => {
    render(<MetricCard title="Interactions" value={1200} />);
    expect(screen.getByText("1,200")).toBeInTheDocument();
  });

  it("renders zero value correctly", () => {
    render(<MetricCard title="Churned" value={0} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders optional description when provided", () => {
    render(
      <MetricCard title="Active" value={30} description="Up 5 this month" />
    );
    expect(screen.getByText("Up 5 this month")).toBeInTheDocument();
  });

  it("does not render description section when omitted", () => {
    render(<MetricCard title="Active" value={30} />);
    expect(screen.queryByText(/up/i)).not.toBeInTheDocument();
  });

  it("renders optional icon slot when provided", () => {
    const icon = <span data-testid="test-icon">★</span>;
    render(<MetricCard title="Metric" value={5} icon={icon} />);
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("applies custom valueClassName to the value element", () => {
    render(
      <MetricCard title="At Risk" value={8} valueClassName="text-red-600" />
    );
    const valueEl = screen.getByText("8");
    expect(valueEl).toHaveClass("text-red-600");
  });

  it("uses default text-foreground class when no valueClassName given", () => {
    render(<MetricCard title="Default" value={3} />);
    const valueEl = screen.getByText("3");
    expect(valueEl).toHaveClass("text-foreground");
  });
});
