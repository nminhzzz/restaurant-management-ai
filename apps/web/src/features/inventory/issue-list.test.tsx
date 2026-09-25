import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { IssueList } from "./issue-list";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const ingredients = [
  { MaNguyenLieu: 1, TenNguyenLieu: "Gạo", DonViTinh: "kg" },
];

describe("IssueList", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    // Radix Select scrolls the highlighted item into view on open; jsdom has no
    // layout engine, so the method is missing outright.
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("shows the API's negative-stock error inline", async () => {
    fetchMock.mockImplementation(
      (path: string, options: { method?: string } = {}) => {
        if (path.startsWith("/catalog/ingredients")) {
          return Promise.resolve({ items: ingredients });
        }
        if (path === "/inventory/issues" && options.method === "POST") {
          return Promise.reject(
            new ApiError(422, "BUSINESS_RULE_VIOLATION", "Không đủ tồn kho."),
          );
        }
        return Promise.resolve([]);
      },
    );

    render(<IssueList />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu xuất" }),
    );

    fireEvent.change(await screen.findByLabelText("Số lượng"), {
      target: { value: "100" },
    });
    // Select defaults to the first ingredient's value only after interaction, so
    // the form still validates ingredient_id; pick it directly via the trigger.
    fireEvent.click(screen.getByRole("combobox", { name: "Nguyên liệu" }));
    fireEvent.click(await screen.findByText("Gạo (kg)"));

    fireEvent.click(screen.getByRole("button", { name: "Ghi nhận xuất kho" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Không đủ tồn kho.",
    );
  });
});
