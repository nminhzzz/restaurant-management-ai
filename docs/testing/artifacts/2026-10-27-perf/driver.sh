#!/bin/bash
# Appendix J driver. MODE=smoke|full. Sequential; logs to $S/driver-$MODE.log
set -u
S=/private/tmp/claude-501/-Users-nmh-work-Mac-NMHx-Personal-KLTN/e1a07314-73b0-40df-a562-46959eecde2a/scratchpad/perf
REPO=/Users/nmh/work/Mac/NMHx/Personal/KLTN
MODE=${MODE:-smoke}
. $S/env.sh
if [ "$MODE" = smoke ]; then
  OUT=$S/smoke; WARM=10; DUR=30; REPS="1"; LEVELS="5"
else
  OUT=$REPO/docs/testing/artifacts/2026-10-27-perf; WARM=120; DUR=600; REPS="1 2 3"; LEVELS="5 10 20"
fi
mkdir -p $OUT
LOG=$S/driver-$MODE.log
ANCHOR=$(cat $S/anchor.txt)
cd $REPO/apps/api
log() { echo "[$(date '+%F %T')] $*" | tee -a $LOG; }

restore() {
  log "restore snapshot"
  docker exec -i restaurant-db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" perf_restaurant' < $S/snapshot.sql 2>>$LOG || log "RESTORE FAILED"
}

start_api() {
  DATABASE_URL="$PERF_URL" PAYMENT_GATEWAY=simulator AI_PROVIDER=fake \
    .venv/bin/uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8001 > $OUT/api-$1.log 2>&1 &
  API_PID=$!
  echo $API_PID > $S/api.pid
  for i in $(seq 1 60); do
    curl -sf http://127.0.0.1:8001/health >/dev/null && { log "api up pid=$API_PID"; return 0; }
    sleep 1
  done
  log "API FAILED TO START"; return 1
}

stop_api() {
  if [ -n "${API_PID:-}" ] && ps -p $API_PID -o command= | grep -q "uvicorn app.main:app"; then
    kill $API_PID; sleep 2; ps -p $API_PID >/dev/null 2>&1 && kill -9 $API_PID
    log "api stopped pid=$API_PID"
  fi
  API_PID=
}

sampler() {  # $1 run id
  local f=$OUT/resources-$1.csv
  echo "time,load1,load5,cpu_idle_pct,db_cpu_pct,db_mem,db_threads_connected,row_lock_time_ms,row_lock_waits,api_cpu_pct,api_rss_kb" > $f
  while true; do
    local t=$(date '+%F %T')
    local ld=$(uptime | sed 's/.*load averages*: //' | awk '{print $1","$2}')
    local idle=$(top -l 1 -n 0 | awk '/CPU usage/ {print $7}' | tr -d '%')
    local ds=$(docker stats --no-stream --format '{{.CPUPerc}},{{.MemUsage}}' restaurant-db | sed 's/ \/ [^,]*//; s/%//')
    local st=$(docker exec restaurant-db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SHOW GLOBAL STATUS WHERE Variable_name IN (\"Threads_connected\",\"Innodb_row_lock_time\",\"Innodb_row_lock_waits\")"' 2>/dev/null | sort | awk '{printf "%s%s", (NR>1?",":""), $2}')
    # sorted: Innodb_row_lock_time, Innodb_row_lock_waits, Threads_connected
    local thr=$(echo $st | cut -d, -f3); local lt=$(echo $st | cut -d, -f1); local lw=$(echo $st | cut -d, -f2)
    local ap=$(ps -p $(cat $S/api.pid) -o %cpu=,rss= 2>/dev/null | awk '{print $1","$2}')
    echo "$t,$ld,$idle,$ds,$thr,$lt,$lw,$ap" >> $f
    sleep 30
  done
}

run_one() {  # kind vu rep
  local kind=$1 vu=$2 rep=$3
  local id=$kind-vu$(printf %02d $vu)-r$rep
  log "=== $id begin head=$(git rev-parse --short HEAD) branch=$(git branch --show-current) dirty_api_scripts=$(git status --short -- ../../apps/api/src ../../scripts | wc -l | tr -d ' ')"
  restore
  start_api $id || return 1
  sampler $id & SPID=$!
  local t0=$(date +%s)
  if [ "$kind" = biz ]; then
    uv run python ../../scripts/load_business.py --base-url http://127.0.0.1:8001 --accounts $S/accounts.json \
      --run-id $id --output $OUT/$id.csv --vu $vu --warmup $WARM --duration $DUR \
      --cache "Không có bộ nhớ đệm báo cáo; thao tác nghiệp vụ không dùng cache" > $OUT/$id.stdout 2>&1
  else
    uv run python ../../scripts/load_reports.py --base-url http://127.0.0.1:8001 --accounts $S/accounts.json \
      --run-id $id --output $OUT/$id.csv --vu 5 --warmup $WARM --duration $DUR \
      --manifest $S/manifest.json --anchor $ANCHOR \
      --cache "Không dùng cache ứng dụng cho doanh thu/xếp hạng món (chỉ /reports/comparison có cache, không được gọi); buffer pool InnoDB vẫn ấm" > $OUT/$id.stdout 2>&1
  fi
  local rc=$?
  log "$id load exit=$rc elapsed=$(( $(date +%s) - t0 ))s"
  kill $SPID 2>/dev/null; wait $SPID 2>/dev/null
  uv run python ../../scripts/verify_perf.py --database-url "$PERF_URL" --baseline $S/manifest.json --output $OUT/verify-$id.json >> $LOG 2>&1
  log "$id verify exit=$?"
  python3 -I $S/slim.py $OUT/verify-$id.json $OUT/verify-$id.slim.json && rm -f $OUT/verify-$id.json
  stop_api
  log "=== $id end"
}

log "driver start MODE=$MODE commit=$(git rev-parse --short HEAD)"
for vu in $LEVELS; do for rep in $REPS; do run_one biz $vu $rep; done; done
for rep in $REPS; do run_one rep 5 $rep; done
restore
log "DRIVER DONE"
