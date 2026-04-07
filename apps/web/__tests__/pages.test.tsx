import { render, screen, fireEvent } from "@testing-library/react";
import type { ComponentProps, ReactNode } from "react";
import { describe, it, expect, vi } from "vitest";

type LinkMockProps = { children?: ReactNode; href: string } & Omit<
  ComponentProps<"a">,
  "href" | "children"
>;

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: LinkMockProps) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe("Sidebar", () => {
  it("renders all navigation items", async () => {
    const { Sidebar } = await import("@/components/sidebar");
    render(<Sidebar />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Assistant")).toBeInTheDocument();
    expect(screen.getByText("Memory")).toBeInTheDocument();
    expect(screen.getByText("Sources")).toBeInTheDocument();
    expect(screen.getByText("Health")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders the app name", async () => {
    const { Sidebar } = await import("@/components/sidebar");
    render(<Sidebar />);
    expect(screen.getByText("Praxo-PICOS")).toBeInTheDocument();
  });
});

describe("StatusCard", () => {
  it("renders title and detail", async () => {
    const { StatusCard } = await import("@/components/status-card");
    render(<StatusCard title="Test Service" status="ok" detail="All good" />);
    expect(screen.getByText("Test Service")).toBeInTheDocument();
    expect(screen.getByText("All good")).toBeInTheDocument();
  });

  it("renders action button when provided", async () => {
    const { StatusCard } = await import("@/components/status-card");
    const onClick = vi.fn();
    render(<StatusCard title="Test" status="warning" action={{ label: "Fix", onClick }} />);
    expect(screen.getByText("Fix")).toBeInTheDocument();
  });
});

describe("OnboardingPage", () => {
  it("renders welcome copy and first step", async () => {
    const OnboardingPage = (await import("@/app/onboarding/page")).default;
    render(<OnboardingPage />);

    expect(
      screen.getByRole("heading", { name: /welcome to praxo-picos/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /pick your memory folder/i })
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("~/Documents/Praxo-PICOS")).toBeInTheDocument();
  });

  it("advances to the next step when Next is clicked", async () => {
    const OnboardingPage = (await import("@/app/onboarding/page")).default;
    render(<OnboardingPage />);

    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(
      screen.getByRole("heading", { name: /choose what to remember/i })
    ).toBeInTheDocument();
  });

  it("disables Back on the first step", async () => {
    const OnboardingPage = (await import("@/app/onboarding/page")).default;
    render(<OnboardingPage />);

    expect(screen.getByRole("button", { name: /^back$/i })).toBeDisabled();
  });
});
