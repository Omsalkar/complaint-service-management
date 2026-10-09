import os, sqlite3
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from common.core import setup_logging, auth_user, internal_key
app=FastAPI(title='Notification Service',version='1.0'); log=setup_logging(); DB='/data/notifications.db'
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
os.makedirs('/data',exist_ok=True); c=db(); c.execute("""CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,message TEXT NOT NULL,complaint_id INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP,is_read INTEGER DEFAULT 0)"""); c.commit(); c.close()
class NotificationIn(BaseModel): user_id:int; message:str; complaint_id:int|None=None
@app.get('/health')
def health(): return {'service':'notification','status':'UP'}
@app.post('/internal/notifications')
def create(x:NotificationIn,_=Depends(internal_key)):
 c=db(); cur=c.execute('INSERT INTO notifications(user_id,message,complaint_id) VALUES(?,?,?)',(x.user_id,x.message,x.complaint_id)); c.commit(); row=c.execute('SELECT * FROM notifications WHERE id=?',(cur.lastrowid,)).fetchone(); c.close(); log.info('notification created user=%s',x.user_id); return dict(row)
@app.get('/notifications')
def list_notifications(user=Depends(auth_user)):
 c=db(); rows=c.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC',(int(user['sub']),)).fetchall(); c.close(); return [dict(r) for r in rows]
@app.patch('/notifications/{nid}/read')
def mark_read(nid:int,user=Depends(auth_user)):
 c=db(); c.execute('UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?',(nid,int(user['sub']))); c.commit(); row=c.execute('SELECT * FROM notifications WHERE id=?',(nid,)).fetchone(); c.close(); return dict(row) if row else {'message':'Not found'}
