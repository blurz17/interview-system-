import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock scrollIntoView for jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn();

// Mock speechSynthesis for jsdom
Object.defineProperty(window, "speechSynthesis", {
  value: {
    speak: vi.fn(),
    cancel: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    getVoices: vi.fn().mockReturnValue([]),
  },
  writable: true,
});

