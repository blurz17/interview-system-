import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { App } from "../src/app/App";

// Mock fetch for health check
global.fetch = vi.fn().mockImplementation(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ status: "ok", app_name: "CareerPilot", version: "1.0.0" }),
  })
);

describe("App Root", () => {
  it("renders navbar and CareerPilot title", async () => {
    render(<App />);
    expect(screen.getByText("CareerPilot")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Welcome to CareerPilot")).toBeInTheDocument();
    });
  });
});
