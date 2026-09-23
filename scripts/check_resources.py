#!/usr/bin/env python3
"""Pre-flight: skip integration if disk/RAM/load is too low. Never crash the host."""

import os
import shutil
import sys

MIN_DISK_GB = 2.0
MIN_MEM_MB = 1024  # free + cached on Linux, or free pages on macOS


def main() -> int:
    ncpu = os.cpu_count() or 4
    # Disk
    try:
        free_gb = shutil.disk_usage(".").free / 1024**3
        if free_gb < MIN_DISK_GB:
            print(
                f"[check-resources] SKIP: disk free {free_gb:.1f}GB < {MIN_DISK_GB}GB — not running integration"
            )
            return 2  # special: caller should skip
    except Exception as e:  # noqa: BLE001
        print(f"[check-resources] warn disk check failed: {e}")

    # Load
    try:
        load1 = os.getloadavg()[0]
        if load1 > 0.9 * ncpu:
            print(
                f"[check-resources] SKIP: load {load1:.1f} > 0.9*{ncpu} — host saturated"
            )
            return 2
    except Exception:  # noqa: BLE001, S110
        pass

    # Memory (best-effort, no psutil)
    try:
        if os.path.exists("/proc/meminfo"):
            d = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    d[k] = int(v.split()[0])  # kB
            avail = d.get("MemAvailable", d.get("MemFree", 0)) // 1024
            if avail < MIN_MEM_MB:
                print(
                    f"[check-resources] SKIP: MemAvailable {avail}MB < {MIN_MEM_MB}MB"
                )
                return 2
        else:
            # macOS: vm_stat free pages
            import subprocess

            out = subprocess.check_output(["vm_stat"], text=True)
            pages = {}
            for ln in out.splitlines():
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    try:
                        pages[k.strip()] = int(v.strip().split()[0].strip("."))
                    except ValueError:
                        pass
            reclaim = (
                pages.get("Pages free", 0)
                + pages.get("Pages inactive", 0)
                + pages.get("Pages speculative", 0)
            )
            reclaim_mb = reclaim * 16384 // 1024 // 1024
            if reclaim_mb < 1024:
                print(
                    f"[check-resources] SKIP: reclaimable {reclaim_mb}MB < 1024MB — host under pressure"
                )
                return 2
    except Exception as e:  # noqa: BLE001
        print(f"[check-resources] warn mem check failed: {e}")

    print(f"[check-resources] OK — proceeding (ncpu={ncpu})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
