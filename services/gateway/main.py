import os, httpx, jwt
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
app=FastAPI(title='Complaint System API Gateway',version='1.0')
SECRET=os.getenv('JWT_SECRET','super-secret-change-me')
ROUTES={'auth':os.getenv('AUTH_URL','http://localhost:8001'),'users':os.getenv('USER_URL','http://localhost:8002'),'complaints':os.getenv('COMPLAINT_URL','http://localhost:8003'),'assignments':os.getenv('ASSIGNMENT_URL','http://localhost:8004'),'notifications':os.getenv('NOTIFICATION_URL','http://localhost:8005')}
PUBLIC={('POST','/api/auth/register'),('POST','/api/auth/login')}
def decode(auth):
 if not auth or not auth.startswith('Bearer '): raise HTTPException(401,'Bearer token required')
 try:return jwt.decode(auth.split(' ',1)[1],SECRET,algorithms=['HS256'])
 except Exception: raise HTTPException(401,'Invalid or expired token')
@app.get('/health')
def health(): return {'service':'api-gateway','status':'UP'}
@app.api_route('/api/{service}/{path:path}',methods=['GET','POST','PUT','PATCH','DELETE'])
async def proxy(service:str,path:str,request:Request):
 if service not in ROUTES: raise HTTPException(404,'Service not found')
 target=ROUTES[service]+'/'+path
 body=await request.body(); headers={k:v for k,v in request.headers.items() if k.lower() not in {'host','content-length'}}
 if (request.method,f'/api/{service}/{path}') not in PUBLIC:
  user=decode(request.headers.get('authorization')); headers['X-User-Id']=str(user['sub']); headers['X-User-Role']=user['role']
  # Services decode the JWT themselves, so keep Authorization.
 async with httpx.AsyncClient(timeout=15) as client:
  r=await client.request(request.method,target,content=body,headers=headers,params=request.query_params)
 return Response(content=r.content,status_code=r.status_code,headers={k:v for k,v in r.headers.items() if k.lower() not in {'content-encoding','transfer-encoding','content-length'}} ,media_type=r.headers.get('content-type'))

# Serve the browser frontend from the same origin as the API gateway.
FRONTEND_DIR = Path(__file__).resolve().parent / 'frontend'
if FRONTEND_DIR.exists():
    app.mount('/', StaticFiles(directory=str(FRONTEND_DIR), html=True), name='frontend')
