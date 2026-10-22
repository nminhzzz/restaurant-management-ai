import { afterEach, describe, expect, it } from "vitest";

import { loadSession, saveSession, sessionSnapshot } from "./session";

const session = { token: "t", role: "MANAGER", username: "quanly" };

afterEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

describe("session persistence", () => {
  it("keeps the login across reloads and new tabs (localStorage)", () => {
    saveSession(session);

    expect(localStorage.getItem("session")).not.toBeNull();
    expect(loadSession()?.token).toBe("t");
  });

  it("drops a session whose stored lifetime has passed", () => {
    localStorage.setItem(
      "session",
      JSON.stringify({ ...session, expires_at: Date.now() - 1000 }),
    );

    expect(loadSession()).toBeNull();
    expect(sessionSnapshot()).toBeNull();
  });

  it("migrates a session left in sessionStorage by the old version", () => {
    sessionStorage.setItem("session", JSON.stringify(session));

    expect(loadSession()?.token).toBe("t");
    expect(localStorage.getItem("session")).not.toBeNull();
    expect(sessionStorage.getItem("session")).toBeNull();
  });
});
