import { createSlice } from "@reduxjs/toolkit";

export interface DashboardState {
  dateRange: { from: string | null; to: string | null };
  isLoading: boolean;
  error: string | null;
}

const initialState: DashboardState = {
  dateRange: { from: null, to: null },
  isLoading: false,
  error: null,
};

export const dashboardSlice = createSlice({
  name: "dashboard",
  initialState,
  reducers: {
    // Reducers will be implemented in Phase 4 (Dashboard Analytics)
  },
});

export default dashboardSlice.reducer;
