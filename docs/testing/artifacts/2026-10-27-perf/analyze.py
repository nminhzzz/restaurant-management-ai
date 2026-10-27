import csv, glob, math, os, sys, json
from collections import defaultdict
D = sys.argv[1]
DUR = 600.0
def pct(v, f):
    if not v: return float("nan")
    o = sorted(v); p = (len(o)-1)*f; lo, hi = math.floor(p), math.ceil(p)
    return o[lo] if lo == hi else o[lo] + (o[hi]-o[lo])*(p-lo)
def load(path):
    with open(path) as f: return [r for r in csv.DictReader(f) if r["phase"] == "measurement"]
def stats(rows):
    ok = [float(r["latency_ms"]) for r in rows if r["outcome"] == "ok"]
    te = sum(r["outcome"] == "technical_error" for r in rows)
    br = sum(r["outcome"] == "business_rejection" for r in rows)
    return dict(n=len(rows), ok=len(ok), p50=pct(ok, .5), p95=pct(ok, .95), tput=len(ok)/DUR, te=te, br=br, terr=te/len(rows) if rows else 0)
def fmt(s): return f"{s['n']} | {s['p50']:.0f} | {s['p95']:.0f} | {s['tput']:.2f} | {s['te']} ({s['terr']*100:.2f}%) | {s['br']}"
BIZ = ["hold","adjust_hold","send","read_order","read_menu","catalog","receipt"]
REP = ["revenue_day","revenue_month","ranking"]
out = []
summary = {}
for kind, ops, levels in (("biz", BIZ, [5,10,20]), ("rep", REP, [5])):
    for vu in levels:
        files = sorted(glob.glob(f"{D}/{kind}-vu{vu:02}-r[0-9].csv"))
        if not files: continue
        data = [load(f) for f in files]
        out.append(f"\n#### {'Nghiệp vụ' if kind=='biz' else 'Báo cáo'} — {vu} VU\n")
        out.append("| Thao tác | Lần chạy | Mẫu | p50 (ms) | p95 (ms) | Thông lượng (req/s) | Lỗi kỹ thuật | Từ chối nghiệp vụ |")
        out.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for op in ops:
            pooled = []
            for i, rows in enumerate(data, 1):
                r = [x for x in rows if x["operation"] == op]; pooled += r
                out.append(f"| {op} | {i} | {fmt(stats(r))} |")
            s = stats(pooled); summary[(kind, vu, op)] = s
            out.append(f"| **{op}** | **gộp 3 lần** | {fmt(s)} |")
print("\n".join(out))
print("\nSUMMARY pooled p95 (ms):")
for k, s in summary.items(): print(k, round(s["p95"]), "n=", s["n"], "te=", s["te"])
# max per-rep p95 for sensitivity
print("\nPER-REP max p95:")
for kind, ops, levels in (("biz", BIZ, [5,10,20]), ("rep", REP, [5])):
    for vu in levels:
        files = sorted(glob.glob(f"{D}/{kind}-vu{vu:02}-r[0-9].csv"))
        for op in ops:
            ps = [stats([x for x in load(f) if x["operation"] == op])["p95"] for f in files]
            if ps: print(kind, vu, op, [round(p) for p in ps])
# resources
print("\nRESOURCES:")
for f in sorted(glob.glob(f"{D}/resources-*.csv")):
    rows = list(csv.DictReader(open(f)))
    if not rows: continue
    g = lambda k: [float(r[k]) for r in rows if r[k] not in ("", None)]
    lt = g("row_lock_time_ms"); lw = g("row_lock_waits")
    mem = [float(r["db_mem"].replace("MiB","").replace("GiB","")) * (1024 if "GiB" in r["db_mem"] else 1) for r in rows]
    print(os.path.basename(f), "n=", len(rows), "load1 avg/max %.1f/%.1f" % (sum(g("load1"))/len(rows), max(g("load1"))),
          "idle%% avg/min %.0f/%.0f" % (sum(g("cpu_idle_pct"))/len(rows), min(g("cpu_idle_pct"))),
          "dbcpu avg/max %.0f/%.0f" % (sum(g("db_cpu_pct"))/len(rows), max(g("db_cpu_pct"))),
          "dbmem max %.0fMiB" % max(mem), "thr max %d" % max(g("db_threads_connected")),
          "lock_ms delta %d waits delta %d" % (lt[-1]-lt[0], lw[-1]-lw[0]),
          "apicpu avg/max %.0f/%.0f" % ((sum(g("api_cpu_pct"))/max(1,len(g("api_cpu_pct")))), max(g("api_cpu_pct") or [0])),
          "apirss max %.0fMB" % (max(g("api_rss_kb") or [0])/1024))
