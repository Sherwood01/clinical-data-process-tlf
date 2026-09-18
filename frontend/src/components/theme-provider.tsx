"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeContextType {
  theme: Theme;
  resolved: "light" | "dark";
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "system",
  resolved: "light",
  setTheme: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

function applyTheme(theme: Theme) {
  let isDark: boolean;
  if (theme === "system") {
    isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  } else {
    isDark = theme === "dark";
  }
  document.documentElement.classList.toggle("dark", isDark);
}

export function ThemeProvider({
  children,
  defaultTheme = "system",
  enableSystem = true,
  disableTransitionOnChange = false,
}: {
  children: React.ReactNode;
  defaultTheme?: Theme;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
}) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);
  const [resolved, setResolved] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);

  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    try {
      localStorage.setItem("theme", newTheme);
    } catch {}
    applyTheme(newTheme);
    // Update resolved
    if (newTheme === "system") {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setResolved(isDark ? "dark" : "light");
    } else {
      setResolved(newTheme);
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("theme") as Theme | null;
    const initial = stored || defaultTheme;
    setThemeState(initial);
    applyTheme(initial);

    if (initial === "system" || stored === null) {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setResolved(isDark ? "dark" : "light");
    } else {
      setResolved(initial as "light" | "dark");
    }

    if (enableSystem) {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = () => {
        const current = localStorage.getItem("theme") as Theme | null;
        if (!current || current === "system") {
          applyTheme("system");
          setResolved(mq.matches ? "dark" : "light");
        }
      };
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [defaultTheme, enableSystem, setTheme]);

  // Prevent flash by not rendering theme-dependent UI until mounted
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, resolved, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
