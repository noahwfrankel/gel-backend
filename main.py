from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.aesthetic import router as aesthetic_router
from routes.fashion import router as fashion_router

load_dotenv(override=False)

app = FastAPI(title="GEL API", version="1.0.0")

# CORS — allow the Vercel frontend and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gel-seven.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(aesthetic_router, prefix="/aesthetic")
app.include_router(fashion_router, prefix="/fashion")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "GEL API"}
