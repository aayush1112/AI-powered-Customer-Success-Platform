import { createSlice } from "@reduxjs/toolkit";

export interface CustomerState {
  selectedCustomerId: string | null;
  filters: Record<string, unknown>;
  isLoading: boolean;
  error: string | null;
}

const initialState: CustomerState = {
  selectedCustomerId: null,
  filters: {},
  isLoading: false,
  error: null,
};

export const customerSlice = createSlice({
  name: "customer",
  initialState,
  reducers: {
    // Reducers will be implemented in Phase 3 (Customer Management)
  },
});

export default customerSlice.reducer;
