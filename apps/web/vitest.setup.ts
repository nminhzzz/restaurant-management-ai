import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// `globals` is off in vitest.config, so Testing Library cannot register its own
// auto-cleanup; without this the DOM of one test leaks into the next.
afterEach(cleanup);
