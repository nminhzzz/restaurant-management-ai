"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { homePathFor } from "@/lib/modules";
import { loadSession } from "@/lib/session";

// The session lives in sessionStorage, so only the browser can tell where to go.
export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace(homePathFor(loadSession()?.role));
  }, [router]);

  return null;
}
