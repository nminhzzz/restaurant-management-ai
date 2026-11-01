import asyncio,json,sys
sys.path.insert(0,'../..')
import httpx,asyncmy
from scripts.bench_load import main
async def run():
 for i in range(40):
  try:
   async with httpx.AsyncClient() as c:
    r=await c.get('http://127.0.0.1:8001/api/v1/health')
   break
  except Exception: await asyncio.sleep(.5)
 accounts=json.load(open('/workspace/scratch/c206e1254747/mysql_runtime/perf_accounts.json'))
 a=accounts[0]['MANAGER']
 conn=await asyncmy.connect(host='127.0.0.1',user='restaurant',password='restaurant',database='perf_codex_0111')
 async with conn.cursor() as cur:
  await cur.execute("SELECT DATE_FORMAT(BusinessDate, '%Y-%m'), COUNT(*) FROM `ORDER` GROUP BY DATE_FORMAT(BusinessDate, '%Y-%m') ORDER BY COUNT(*) DESC LIMIT 1")
  month,count=await cur.fetchone()
 conn.close()
 from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
 from scripts.perf.verify import verify
 eng=create_async_engine('mysql+asyncmy://restaurant:restaurant@127.0.0.1:3306/perf_codex_0111?charset=utf8mb4')
 async with async_sessionmaker(eng,expire_on_commit=False)() as session:
  failures=await verify(session)
 await eng.dispose()
 json.dump({'failures':failures,'count':len(failures)},open('/workspace/scratch/c206e1254747/full_test_evidence/partial_integrity.json','w'),indent=2)
 print('Dataset integrity failures:',failures,flush=True)
 print('Populated benchmark month:',month,'orders:',count,flush=True)
 json.dump({'month':month,'orders_in_month':count,'requests_per_endpoint':60,'concurrency':20,'dataset_complete':False},open('/workspace/scratch/c206e1254747/full_test_evidence/load_scope.json','w'),indent=2)
 return await main('http://127.0.0.1:8001',month,60,20,2.0,a['username'],a['password'])
sys.exit(asyncio.run(run()))
