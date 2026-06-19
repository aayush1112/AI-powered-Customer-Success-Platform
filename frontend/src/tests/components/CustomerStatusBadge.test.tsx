import { render, screen } from "@testing-library/react";
import { CustomerStatusBadge } from "@/features/customers/components/CustomerStatusBadge";

describe("CustomerStatusBadge", () => {
  it("renders 'Active' for ACTIVE status", () => {
    render(<CustomerStatusBadge status="ACTIVE" />);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders 'At Risk' for AT_RISK status", () => {
    render(<CustomerStatusBadge status="AT_RISK" />);
    expect(screen.getByText("At Risk")).toBeInTheDocument();
  });

  it("renders 'Churned' for CHURNED status", () => {
    render(<CustomerStatusBadge status="CHURNED" />);
    expect(screen.getByText("Churned")).toBeInTheDocument();
  });

  it("renders 'Prospect' for PROSPECT status", () => {
    render(<CustomerStatusBadge status="PROSPECT" />);
    expect(screen.getByText("Prospect")).toBeInTheDocument();
  });

  it("renders a badge element", () => {
    render(<CustomerStatusBadge status="ACTIVE" />);
    const badge = screen.getByText("Active");
    expect(badge).toBeInTheDocument();
    // Badge is rendered as a div/span with the variant class applied
    expect(badge.tagName).not.toBe("INPUT");
  });
});
