import sqlite3, os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from common.core import setup_logging, auth_user, internal_key
app=FastAPI(title='User Service',version='1.0'); log=setup_logging(); DB='/data/users.db'
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
os.makedirs('/data',exist_ok=True); c=db(); c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL)'); c.commit(); c.close()
class UserIn(BaseModel): name:str; email:str
class UserOut(UserIn): id:int
@app.get('/health')
def health(): return {'service':'user','status':'UP'}
@app.post('/internal/users',response_model=UserOut)
def internal_create(x:UserIn, _=Depends(internal_key)):
 c=db(); c.execute('INSERT OR REPLACE INTO users(id,name,email) VALUES(COALESCE((SELECT id FROM users WHERE email=?),NULL),?,?)',(x.email,x.name,x.email)); c.commit(); row=c.execute('SELECT * FROM users WHERE email=?',(x.email,)).fetchone(); c.close(); return dict(row)
@app.get('/users/me',response_model=UserOut)
def me(user=Depends(auth_user)):
 c=db(); row=c.execute('SELECT * FROM users WHERE id=?',(int(user['sub']),)).fetchone(); c.close()
 if not row: raise HTTPException(404,'Profile not found')
 return dict(row)
@app.get('/users',response_model=list[UserOut])
def list_users(user=Depends(auth_user)):
 if user['role']!='ADMIN': raise HTTPException(403,'Admin only')
 c=db(); rows=c.execute('SELECT * FROM users ORDER BY id').fetchall(); c.close(); return [dict(r) for r in rows]
