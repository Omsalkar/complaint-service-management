import os, sqlite3, httpx
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from common.core import setup_logging, auth_user, internal_key
app=FastAPI(title='Complaint Service',version='1.0'); log=setup_logging(); DB='/data/complaints.db'; NOTIFY=os.getenv('NOTIFICATION_URL','http://localhost:8005'); KEY=os.getenv('INTERNAL_API_KEY','college-project-key')
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
os.makedirs('/data',exist_ok=True); c=db(); c.execute("""CREATE TABLE IF NOT EXISTS complaints(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,title TEXT NOT NULL,description TEXT NOT NULL,category TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'OPEN',assigned_to INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"""); c.commit(); c.close()
class ComplaintIn(BaseModel): title:str; description:str; category:str
class StatusIn(BaseModel): status:str
class AssignIn(BaseModel): assignee_id:int
async def notify(user_id,message,complaint_id):
 try:
  async with httpx.AsyncClient(timeout=4) as client: await client.post(NOTIFY+'/internal/notifications',json={'user_id':user_id,'message':message,'complaint_id':complaint_id},headers={'X-Internal-Key':KEY})
 except Exception as e: log.error('notification failed: %s',e)
@app.get('/health')
def health(): return {'service':'complaint','status':'UP'}
@app.post('/complaints')
async def create(x:ComplaintIn,user=Depends(auth_user)):
 c=db(); cur=c.execute('INSERT INTO complaints(user_id,title,description,category) VALUES(?,?,?,?)',(int(user['sub']),x.title,x.description,x.category)); c.commit(); cid=cur.lastrowid; row=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone(); c.close(); await notify(int(user['sub']),f'Complaint #{cid} registered successfully',cid); return dict(row)
@app.get('/complaints')
def list_all(user=Depends(auth_user)):
 c=db()
 if user['role']=='ADMIN': rows=c.execute('SELECT * FROM complaints ORDER BY id DESC').fetchall()
 else: rows=c.execute('SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC',(int(user['sub']),)).fetchall()
 c.close(); return [dict(r) for r in rows]
@app.get('/complaints/{cid}')
def get(cid:int,user=Depends(auth_user)):
 c=db(); row=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone(); c.close()
 if not row: raise HTTPException(404,'Complaint not found')
 if user['role']!='ADMIN' and row['user_id']!=int(user['sub']): raise HTTPException(403,'Not allowed')
 return dict(row)
@app.patch('/complaints/{cid}/status')
async def status(cid:int,x:StatusIn,user=Depends(auth_user)):
 allowed={'OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED','REJECTED'}
 if x.status not in allowed: raise HTTPException(400,'Invalid status')
 c=db(); row=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone()
 if not row: c.close(); raise HTTPException(404,'Complaint not found')
 if user['role']!='ADMIN' and row['assigned_to']!=int(user['sub']): c.close(); raise HTTPException(403,'Admin or assigned employee only')
 c.execute('UPDATE complaints SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(x.status,cid)); c.commit(); row=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone(); c.close(); await notify(row['user_id'],f'Complaint #{cid} status changed to {x.status}',cid); return dict(row)
@app.patch('/internal/complaints/{cid}/assignment')
async def assign(cid:int,x:AssignIn,_=Depends(internal_key)):
 c=db(); row=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone()
 if not row: c.close(); raise HTTPException(404,'Complaint not found')
 c.execute('UPDATE complaints SET assigned_to=?,status="ASSIGNED",updated_at=CURRENT_TIMESTAMP WHERE id=?',(x.assignee_id,cid)); c.commit(); row=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone(); c.close(); await notify(row['user_id'],f'Complaint #{cid} assigned to user #{x.assignee_id}',cid); return dict(row)
