import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UserTable } from "@/features/admin/components/UserTable";
import type { UserResponse } from "@/features/admin/types";

const makeUser = (overrides?: Partial<UserResponse>): UserResponse => ({
  id: "00000000-0000-0000-0000-000000000001",
  first_name: "Alice",
  last_name: "Admin",
  email: "alice@example.com",
  role: "ADMIN",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  ...overrides,
});

describe("UserTable", () => {
  it("renders empty state when no users", () => {
    render(<UserTable users={[]} onEdit={jest.fn()} />);
    expect(screen.getByText(/no users found/i)).toBeInTheDocument();
  });

  it("renders a row for each user", () => {
    const users = [
      makeUser({ id: "1", first_name: "Alice", last_name: "Admin" }),
      makeUser({ id: "2", first_name: "Bob", last_name: "Manager", role: "MANAGER" }),
    ];
    render(<UserTable users={users} onEdit={jest.fn()} />);
    expect(screen.getByText("Alice Admin")).toBeInTheDocument();
    expect(screen.getByText("Bob Manager")).toBeInTheDocument();
  });

  it("shows role badge for each user", () => {
    const users = [
      makeUser({ role: "ADMIN" }),
      makeUser({ id: "2", role: "VIEWER" }),
    ];
    render(<UserTable users={users} onEdit={jest.fn()} />);
    expect(screen.getByText("Admin")).toBeInTheDocument();
    expect(screen.getByText("Viewer")).toBeInTheDocument();
  });

  it("shows Active badge for active users and Inactive for deactivated", () => {
    const users = [
      makeUser({ is_active: true }),
      makeUser({ id: "2", is_active: false }),
    ];
    render(<UserTable users={users} onEdit={jest.fn()} />);
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("calls onEdit with the correct user when edit button is clicked", async () => {
    const onEdit = jest.fn();
    const user = makeUser();
    render(<UserTable users={[user]} onEdit={onEdit} />);

    const editButton = screen.getByRole("button", { name: /edit alice admin/i });
    await userEvent.click(editButton);

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledWith(user);
  });

  it("renders an edit button for each user", () => {
    const users = [
      makeUser({ id: "1", first_name: "Alice", last_name: "A" }),
      makeUser({ id: "2", first_name: "Bob", last_name: "B" }),
    ];
    render(<UserTable users={users} onEdit={jest.fn()} />);
    expect(screen.getAllByRole("button").length).toBe(2);
  });

  it("displays the user email", () => {
    render(<UserTable users={[makeUser()]} onEdit={jest.fn()} />);
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
  });
});
