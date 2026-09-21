import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ModulePlaceholder } from "@/components/module-placeholder";
import { MODULES } from "@/lib/modules";

describe("ModulePlaceholder", () => {
  it("shows the module title, requirement range and owner", () => {
    render(<ModulePlaceholder descriptor={MODULES.inventory} />);

    expect(
      screen.getByRole("heading", { name: "Quản lý kho" }),
    ).toBeInTheDocument();
    expect(screen.getByText("FR-INV-01 … FR-INV-15")).toBeInTheDocument();
    expect(screen.getByText(/Phụ trách: Minh/)).toBeInTheDocument();
  });
});
