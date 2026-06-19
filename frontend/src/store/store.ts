import { configureStore } from "@reduxjs/toolkit";
import { authSlice } from "./slices/authSlice";
import { customerSlice } from "./slices/customerSlice";
import { interactionSlice } from "./slices/interactionSlice";
import { dashboardSlice } from "./slices/dashboardSlice";
import { baseApi } from "@/services/api/baseApi";

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    customer: customerSlice.reducer,
    interaction: interactionSlice.reducer,
    dashboard: dashboardSlice.reducer,
    [baseApi.reducerPath]: baseApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({ serializableCheck: false }).concat(baseApi.middleware),
  devTools: process.env.NODE_ENV !== "production",
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
