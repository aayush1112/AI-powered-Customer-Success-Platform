"use client";

import { type ReactNode } from "react";
import { Provider as ReduxProvider } from "react-redux";
import { store } from "@/store/store";
import { ThemeProvider } from "./ThemeProvider";
import { AuthInitializer } from "./AuthInitializer";
import { Toaster } from "@/components/ui/toaster";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ReduxProvider store={store}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        {/* Silently re-hydrates auth state on every page load */}
        <AuthInitializer />
        {children}
        <Toaster />
      </ThemeProvider>
    </ReduxProvider>
  );
}
