import { useEffect } from "react";
import { isDesktop } from "../services/host-adapter";

export function useDesktopIntegration() {
  useEffect(() => {
    if (!isDesktop() || !window.wrightDesktop) return;

    const unsubscribe = window.wrightDesktop.onThemeChange(({ theme }) => {
      document.documentElement.setAttribute("data-theme", theme);
    });

    return () => {
      unsubscribe();
    };
  }, []);
}
