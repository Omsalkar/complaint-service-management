import os, sqlite3, httpx
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from common.core import setup_logging, auth_user, internal_key
app=FastAPI(title='Assignment Service',version='1.0'); log=setup_logging(); DB='/data/assignments.db'; COMPLAINT=os.getenv('COMPLAINT_URL','http://localhost:8003'); NOTIFY=os.getenv('NOTIFICATION_URL','http://localhost:8005'); KEY=os.getenv('INTERNAL_API_KEY','college-project-key')
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
os.makedirs('/data',exist_ok=True); c=db(); c.execute("""CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY AUTOINCREMENT,complaint_id INTEGER NOT NULL,assignee_id INTEGER NOT NULL,note TEXT,assigned_at TEXT DEFAULT CURRENT_TIMESTAMP)"""); c.commit(); c.close()
class AssignmentIn(BaseModel): complaint_id:int; assignee_id:int; note:str=''
@app.get('/health')
def health(): return {'service':'assignment','status':'UP'}
@app.post('/assignments')
async def assign(x:AssignmentIn,user=Depends(auth_user)):
 if user['role']!='ADMIN': raise HTTPException(403,'Admin only')
 async with httpx.AsyncClient(timeout=5) as client:
  r=await client.patch(f'{COMPLAINT}/internal/complaints/{x.complaint_id}/assignment',json={'assignee_id':x.assignee_id},headers={'X-Internal-Key':KEY})
  if r.status_code>=400: raise HTTPException(r.status_code,r.text)
 c=db(); cur=c.execute('INSERT INTO assignments(complaint_id,assignee_id,note) VALUES(?,?,?)',(x.complaint_id,x.assignee_id,x.note)); c.commit(); row=c.execute('SELECT * FROM assignments WHERE id=?',(cur.lastrowid,)).fetchone(); c.close(); return dict(row)
@app.get('/assignments')
def list_assignments(user=Depends(auth_user)):
 if user['role']!='ADMIN': raise HTTPException(403,'Admin only')
 c=db(); rows=c.execute('SELECT * FROM assignments ORDER BY id DESC').fetchall(); c.close(); return [dict(r) for r in rows]
