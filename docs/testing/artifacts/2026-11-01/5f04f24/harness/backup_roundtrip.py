import asyncio,json,hashlib,time,os,subprocess
from datetime import datetime,date,time as dtime
from decimal import Decimal
import asyncmy,httpx
from sqlalchemy import select,text,DateTime,Date,Time,Numeric
from sqlalchemy.ext.asyncio import create_async_engine
import app.modules.catalog.models,app.modules.inventory.models,app.modules.sales.models,app.modules.settings.models,app.modules.ai.models,app.shared.audit
from app.shared.base import Base
P='/workspace/scratch/c206e1254747/full_test_evidence'
SRC='mysql+asyncmy://restaurant:restaurant@127.0.0.1:3306/perf_codex_0111?charset=utf8mb4'
DST='mysql+asyncmy://restaurant:restaurant@127.0.0.1:3306/perf_restore_0111?charset=utf8mb4'
def canonical(row):
 def val(v):
  if isinstance(v,Decimal):return format(v,'f')
  if isinstance(v,(datetime,date,dtime)):return v.isoformat()
  return v
 return {k:val(v) for k,v in row.items()}
async def fingerprints(engine):
 result={}
 async with engine.connect() as c:
  for t in Base.metadata.sorted_tables:
   rows=(await c.execute(select(t).order_by(*t.primary_key.columns))).mappings().all()
   b=json.dumps([canonical(dict(r)) for r in rows],sort_keys=True,ensure_ascii=False,default=str).encode()
   result[t.name]={'rows':len(rows),'sha256':hashlib.sha256(b).hexdigest()}
 return result
async def main():
 start=time.perf_counter()
 accounts=json.load(open('/workspace/scratch/c206e1254747/mysql_runtime/perf_accounts.json'))
 a=accounts[0]['MANAGER']
 source=create_async_engine(SRC); target=create_async_engine(DST)
 async with httpx.AsyncClient(base_url='http://127.0.0.1:8001',timeout=120) as client:
  login=await client.post('/api/v1/settings/auth/login',json={'username':a['username'],'password':a['password']});login.raise_for_status()
  token=login.json()['access_token']
  before=await fingerprints(source)
  r=await client.post('/api/v1/settings/backup?include_credentials=true',headers={'Authorization':'Bearer '+token});r.raise_for_status()
  payload=r.json()
  if 'data' not in payload:raise ValueError('Unexpected backup structure')
 conn=await asyncmy.connect(host='127.0.0.1',user='root',autocommit=True)
 async with conn.cursor() as cur:
  await cur.execute('CREATE DATABASE perf_restore_0111 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
  await cur.execute("GRANT ALL PRIVILEGES ON perf_restore_0111.* TO 'restaurant'@'%'")
 conn.close()
 env=os.environ.copy();env['DATABASE_URL']=DST
 with open(P+'/restore_migration.log','w') as log:
  p=await asyncio.create_subprocess_exec('.venv/bin/alembic','upgrade','head',env=env,stdout=log,stderr=log)
  if await p.wait()!=0:raise RuntimeError('restore migration failed')
 async with target.begin() as c:
  await c.execute(text('SET FOREIGN_KEY_CHECKS=0'))
  for table in reversed(Base.metadata.sorted_tables):
   await c.execute(table.delete())
  for t in Base.metadata.sorted_tables:
   rows=[]
   for raw in payload['data'][t.name]:
    row={}
    for col in t.columns:
     if col.computed is not None or col.name not in raw:continue
     v=raw[col.name]
     if v is not None:
      if isinstance(col.type,DateTime):v=datetime.fromisoformat(v.replace('Z','+00:00')).replace(tzinfo=None)
      elif isinstance(col.type,Date):v=date.fromisoformat(v)
      elif isinstance(col.type,Time):v=dtime.fromisoformat(v)
      elif isinstance(col.type,Numeric):v=Decimal(str(v))
     row[col.name]=v
    rows.append(row)
   for offset in range(0,len(rows),500):
    await c.execute(t.insert(),rows[offset:offset+500])
  await c.execute(text('SET FOREIGN_KEY_CHECKS=1'))
 after=await fingerprints(target)
 mismatch=[name for name in before if before[name]!=after[name]]
 result={'tables':len(before),'source_rows':sum(x['rows'] for x in before.values()),'mismatch':mismatch,'seconds':round(time.perf_counter()-start,3),'before':before,'after':after}
 open(P+'/backup_roundtrip.json','w').write(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k not in ('before','after')},ensure_ascii=False),flush=True)
 await source.dispose();await target.dispose()
 assert not mismatch,mismatch
backup_error = None
try:
 asyncio.run(main())
except Exception as exc:
 import traceback
 traceback.print_exc()
 backup_error = exc
# Repeat the exploratory read benchmark against a month that contains data.
with open(P+'/load_populated_month.log','w') as log:
 load_result=subprocess.run(['.venv/bin/python','/workspace/scratch/c206e1254747/mysql_runtime/load.py'],stdout=log,stderr=log)
open(P+'/load_populated_exit.txt','w').write(str(load_result.returncode)+'\n')
# Run the repository gate on the unchanged source with MySQL still available.
env=os.environ.copy();env['PATH']='/workspace/scratch/c206e1254747/test_tools:'+env['PATH']
with open(P+'/gate_final.log','w') as log:
 result=subprocess.run(['make','gate'],cwd='../..',env=env,stdout=log,stderr=log)
open(P+'/gate_final_exit.txt','w').write(str(result.returncode)+'\n')

if backup_error is not None:
 raise backup_error
