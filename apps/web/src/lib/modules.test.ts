import { describe, expect, it } from "vitest";

import { MODULES, MODULE_LIST } from "@/lib/modules";

describe("module registry", () => {
  it("exposes the six business modules in navigation order", () => {
    expect(MODULE_LIST.map((descriptor) => descriptor.key)).toEqual([
      "catalog",
      "sales",
      "inventory",
      "reports",
      "settings",
      "assistant",
    ]);
  });

  it("indexes every module by its key", () => {
    expect(Object.keys(MODULES)).toHaveLength(MODULE_LIST.length);
    for (const descriptor of MODULE_LIST) {
      expect(MODULES[descriptor.key]).toBe(descriptor);
    }
  });

  it("uses unique, absolute paths", () => {
    const paths = MODULE_LIST.map((descriptor) => descriptor.path);

    expect(new Set(paths).size).toBe(paths.length);
    for (const path of paths) {
      expect(path.startsWith("/")).toBe(true);
    }
  });
});
