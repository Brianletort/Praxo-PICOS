import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

function Smoke() {
  return <h1>Praxo-PICOS</h1>;
}

describe("smoke", () => {
  it("renders title", () => {
    render(<Smoke />);
    expect(
      screen.getByRole("heading", { name: /praxo-picos/i })
    ).toBeInTheDocument();
  });
});
