import { createSlice } from "@reduxjs/toolkit";

export interface InteractionState {
  selectedInteractionId: string | null;
  filters: Record<string, unknown>;
  isLoading: boolean;
  error: string | null;
}

const initialState: InteractionState = {
  selectedInteractionId: null,
  filters: {},
  isLoading: false,
  error: null,
};

export const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    // Reducers will be implemented in Phase 3 (Interaction Management)
  },
});

export default interactionSlice.reducer;
