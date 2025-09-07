from fastapi import FastAPI
app=FastAPI()
@app.get('/v1/healthz')
def healthz(): return {'status':'ok'}
