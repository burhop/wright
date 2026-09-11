import { useEffect } from "react";
import { isDesktop } from "../services/host-adapter";
import { applyTheme } from "../services/ui-preferences";

export function useDesktopIntegration() {
  useEffect(() => {
    if (!isDesktop() || !window.wrightDesktop) return;

    const unsubscribe = window.wrightDesktop.onThemeChange(({ theme }) => {
      applyTheme(theme);
    });

    return () => {
      unsubscribe();
    };
  }, []);
}
