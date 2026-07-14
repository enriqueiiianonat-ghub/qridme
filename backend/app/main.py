from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.idrecords.router import router as idrecords_router

app = FastAPI(title="QRIDME Identity Registry Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(idrecords_router)

@app.get("/")
def health():
    return {"status": "ok"}
