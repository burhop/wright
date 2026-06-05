/// <reference types="vitest/globals" />
import "@testing-library/jest-dom";

// Mock IntersectionObserver for components that use it
class MockIntersectionObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  value: MockIntersectionObserver,
});

// Mock matchMedia for responsive components
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock scrollTo
window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;

// Suppress console noise in tests unless explicitly testing logging
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    // Allow React act() warnings through
    if (typeof args[0] === "string" && args[0].includes("act(")) {
      originalError(...args);
    }
  };
});
afterAll(() => {
  console.error = originalError;
});
