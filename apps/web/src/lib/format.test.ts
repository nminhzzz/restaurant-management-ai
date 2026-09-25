import { describe, expect, it } from "vitest";

import { formatDate, formatNumber, formatVnd } from "@/lib/format";
import { roleLabel } from "@/lib/roles";
import { statusTone } from "@/lib/status";

describe("formatVnd", () => {
  it("formats numbers and Decimal strings the same way", () => {
    expect(formatVnd(185000)).toBe("185.000 ₫");
    expect(formatVnd("185000.00")).toBe("185.000 ₫");
  });

  it("renders nothing for missing or non-numeric input", () => {
    expect(formatVnd(null)).toBe("");
    expect(formatVnd(undefined)).toBe("");
    expect(formatVnd("abc")).toBe("");
  });
});

describe("formatNumber", () => {
  it("uses the Vietnamese decimal comma", () => {
    expect(formatNumber(3.25)).toBe("3,25");
    expect(formatNumber("12")).toBe("12");
  });
});

describe("formatDate", () => {
  it("turns an ISO business date into dd/mm/yyyy", () => {
    expect(formatDate("2026-09-25")).toBe("25/09/2026");
  });

  it("passes non-ISO values through and blanks empty ones", () => {
    expect(formatDate("Tuần 39")).toBe("Tuần 39");
    expect(formatDate(null)).toBe("");
  });
});

describe("roleLabel", () => {
  it("shows the Vietnamese name of each role", () => {
    expect(roleLabel("MANAGER")).toBe("Quản lý");
    expect(roleLabel("CASHIER")).toBe("Thu ngân");
    expect(roleLabel("WAREHOUSE")).toBe("Thủ kho");
  });

  it("falls back to the raw value for an unknown role", () => {
    expect(roleLabel("AUDITOR")).toBe("AUDITOR");
  });
});

describe("statusTone", () => {
  it("maps stored statuses onto the semantic tones", () => {
    expect(statusTone("Hoạt động")).toBe("success");
    expect(statusTone("Chờ đối soát")).toBe("warning");
    expect(statusTone("Hết nguyên liệu")).toBe("danger");
    expect(statusTone("Đang mở")).toBe("primary");
    expect(statusTone("Nháp")).toBe("muted");
  });

  it("treats unknown or missing statuses as neutral", () => {
    expect(statusTone("Không rõ")).toBe("neutral");
    expect(statusTone(null)).toBe("neutral");
  });
});
