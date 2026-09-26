import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();
let search = "";
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/sales",
  useSearchParams: () => new URLSearchParams(search),
}));
vi.mock("./floor-step", () => ({
  FloorStep: (p: {
    onNewOrder: (t: number | null) => void;
    onPay: (o: number, t: number | null) => void;
  }) => (
    <div>
      <button onClick={() => p.onNewOrder(4)}>mock-new</button>
      <button onClick={() => p.onPay(142, 4)}>mock-pay</button>
    </div>
  ),
}));
vi.mock("./order-step", () => ({ OrderStep: () => <p>order-step</p> }));
vi.mock("./order-detail", () => ({ OrderDetail: () => <p>order-detail</p> }));
vi.mock("./payment-panel", () => ({
  PaymentPanel: () => <p>payment-panel</p>,
}));
vi.mock("./done-step", () => ({ DoneStep: () => <p>done-step</p> }));

import { SalesWorkspace } from "./sales-workspace";

describe("SalesWorkspace", () => {
  beforeEach(() => {
    replace.mockReset();
    search = "";
  });

  it("starts on the floor and keeps the next step in the URL", () => {
    render(<SalesWorkspace />);
    fireEvent.click(screen.getByText("mock-new"));
    expect(replace).toHaveBeenCalledWith("/sales?step=order&table=4");
    fireEvent.click(screen.getByText("mock-pay"));
    expect(replace).toHaveBeenCalledWith("/sales?step=pay&table=4&order=142");
  });

  it("restores the pay step from the URL", () => {
    search = "step=pay&table=4&order=142";
    render(<SalesWorkspace />);
    expect(screen.getByText("payment-panel")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Thanh toán/ })).toHaveAttribute(
      "aria-current",
      "step",
    );
  });

  it("does not allow jumping to payment without an order", () => {
    search = "step=order&table=4";
    render(<SalesWorkspace />);
    expect(screen.getByRole("button", { name: /Thanh toán/ })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /Chọn bàn/ }));
    expect(replace).toHaveBeenCalledWith("/sales");
  });
});
