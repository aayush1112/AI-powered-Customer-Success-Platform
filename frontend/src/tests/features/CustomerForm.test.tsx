import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { CustomerForm } from "@/features/customers/components/CustomerForm";
import { baseApi } from "@/services/api/baseApi";

function renderWithStore(ui: React.ReactElement) {
  const store = configureStore({
    reducer: { [baseApi.reducerPath]: baseApi.reducer },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware),
  });
  return render(<Provider store={store}>{ui}</Provider>);
}

const defaultProps = {
  mode: "create" as const,
  onSubmit: jest.fn().mockResolvedValue(undefined),
  isLoading: false,
};

describe("CustomerForm — create mode", () => {
  it("renders all required fields", () => {
    renderWithStore(<CustomerForm {...defaultProps} />);
    expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contact name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contact email/i)).toBeInTheDocument();
  });

  it("shows validation errors for empty required fields", async () => {
    renderWithStore(<CustomerForm {...defaultProps} />);
    await userEvent.click(screen.getByRole("button", { name: /create|save/i }));
    await waitFor(() => {
      expect(screen.getAllByRole("alert").length).toBeGreaterThan(0);
    });
  });

  it("shows email validation error for invalid email", async () => {
    renderWithStore(<CustomerForm {...defaultProps} />);
    const emailInput = screen.getByLabelText(/contact email/i);
    await userEvent.type(emailInput, "not-an-email");
    await userEvent.click(screen.getByRole("button", { name: /create|save/i }));
    await waitFor(() => {
      expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
    });
  });

  it("submit button has accessible label", () => {
    renderWithStore(<CustomerForm {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: /create|save/i })
    ).toBeInTheDocument();
  });
});
