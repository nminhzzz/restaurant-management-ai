import { describe, expect, it } from "vitest";

import { statusTone } from "./status";

describe("statusTone", () => {
  it("marks a voucher waiting for approval as a warning and a rejected one as danger", () => {
    expect(statusTone("Chờ duyệt")).toBe("warning");
    expect(statusTone("Đã từ chối")).toBe("danger");
    expect(statusTone("Đã xác nhận")).toBe("success");
  });
});
