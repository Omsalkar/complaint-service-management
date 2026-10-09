import os, sqlite3, httpx
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from common.core import setup_logging, hash_password, verify_password, create_token, auth_user, internal_key

app=FastAPI(title="Authentication Service", version="1.0")
log=setup_logging(); DB="/data/auth.db"; USER_URL=os.getenv("USER_SERVICE_URL","http://localhost:8002")

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    os.makedirs('/data',exist_ok=True)
    c=db(); c.execute("""CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'USER')""")
    c.commit()
    for email,pwd,role in [('admin@example.com','Admin@123','ADMIN'),('user@example.com','User@123','USER')]:
        try:c.execute('INSERT INTO accounts(email,password_hash,role) VALUES(?,?,?)',(email,hash_password(pwd),role)); c.commit()
        except sqlite3.IntegrityError: pass
    c.close()
init()
class Register(BaseModel):
    name:str; email:EmailStr; password:str
class Login(BaseModel):
    email:EmailStr; password:str

@app.get('/health')
def health(): return {'service':'auth','status':'UP'}
@app.post('/register')
async def register(x:Register):
    c=db()
    try:
        cur=c.execute('INSERT INTO accounts(email,password_hash,role) VALUES(?,?,?)',(x.email,hash_password(x.password),'USER')); c.commit(); uid=cur.lastrowid
    except sqlite3.IntegrityError: c.close(); raise HTTPException(409,'Email already registered')
    c.close()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r=await client.post(USER_URL+'/internal/users',json={'id':uid,'name':x.name,'email':x.email},headers={'X-Internal-Key':os.getenv('INTERNAL_API_KEY','college-project-key')}); r.raise_for_status()
    except Exception as e:
        log.error('profile creation failed: %s',e)
    return {'id':uid,'email':x.email,'role':'USER','message':'Registration successful'}

@app.post('/login')
def login(x:Login):
    c=db(); row=c.execute('SELECT * FROM accounts WHERE email=?',(x.email,)).fetchone(); c.close()
    if not row or not verify_password(x.password,row['password_hash']): raise HTTPException(401,'Invalid email or password')
    token=create_token(row['id'],row['role'],row['email']); log.info('login user=%s',row['id'])
    return {'access_token':token,'token_type':'bearer','user':{'id':row['id'],'email':row['email'],'role':row['role']}}

@app.get('/me')
def me(user=Depends(auth_user)): return user
@app.post('/validate')
def validate(user=Depends(auth_user)): return {'valid':True,'user':user}
