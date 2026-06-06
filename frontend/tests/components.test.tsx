import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RiskBadge } from "@/components/RiskBadge";
import { QuotaCard } from "@/components/QuotaCard";

describe("RiskBadge", () => {
  it.each(["low", "medium", "high"] as const)("renders %s with label", (b) => {
    render(<RiskBadge band={b} />);
    expect(screen.getByText(new RegExp(`${b} risk`, "i"))).toBeInTheDocument();
  });
});

describe("QuotaCard", () => {
  it("shows infinity when limit is zero", () => {
    render(<QuotaCard title="API" used={5} limit={0} remaining={0} />);
    expect(screen.getByText(/No limit configured/i)).toBeInTheDocument();
    expect(screen.getByText(/∞/)).toBeInTheDocument();
  });

  it("flags low remaining", () => {
    render(<QuotaCard title="AI" used={95} limit={100} remaining={5} />);
    expect(screen.getByText(/5 left/)).toBeInTheDocument();
  });

  it("flags exhausted quota", () => {
    render(<QuotaCard title="AI" used={100} limit={100} remaining={0} />);
    expect(screen.getByText(/0 left/)).toBeInTheDocument();
  });
});
