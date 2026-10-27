import csv,glob,math
def pct(v,f):
    o=sorted(v);p=(len(o)-1)*f;lo,hi=math.floor(p),math.ceil(p)
    return o[lo] if lo==hi else o[lo]+(o[hi]-o[lo])*(p-lo)
for vu in (5,10,20):
    rows=[]
    for f in sorted(glob.glob(f"biz-vu{vu:02}-r[0-9].csv")):
        rows+=[r for r in csv.DictReader(open(f)) if r["phase"]=="measurement"]
    print("VU",vu)
    for op in ["hold","adjust_hold","send","read_order","read_menu","catalog","receipt"]:
        r=[x for x in rows if x["operation"]==op]
        ok=[float(x["latency_ms"]) for x in r if x["outcome"]=="ok"]
        al=[float(x["latency_ms"]) for x in r if x["outcome"]!="business_rejection"]
        print(f"  {op:12} p95_ok={pct(ok,.95):.0f} p95_incl_err={pct(al,.95):.0f} p99_ok={pct(ok,.99):.0f} max_ok={max(ok):.0f} >1s={sum(v>1000 for v in ok)} ({sum(v>1000 for v in ok)/len(ok)*100:.2f}%)")
