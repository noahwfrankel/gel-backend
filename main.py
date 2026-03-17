import os
import logging

# =============================================================================
# ENV VAR FIX: Only load .env file in local development.
# Railway injects env vars directly into the process — load_dotenv() can
# interfere by setting empty values from a committed .env file.
# =============================================================================
RAILWAY_ENV = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_SERVICE_NAME")

if not RAILWAY_ENV:
    # Local development — load .env file
    from dotenv import load_dotenv
    load_dotenv()
    print("[ENV] Running locally — loaded .env file")
else:
    print(f"[ENV] Running on Railway ({RAILWAY_ENV}) — using injected env vars")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.aesthetic import router as aesthetic_router
from routes.fashion import router as fashion_router

app = FastAPI(title="GEL API", version="1.0.0")

# CORS — allow frontend origins
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

# Register routes
app.include_router(aesthetic_router, prefix="/aesthetic")
app.include_router(fashion_router, prefix="/fashion")


@app.get("/")
async def health():
    return {"status": "ok", "service": "GEL API"}


@app.get("/debug")
async def debug():
    """
    Diagnostic endpoint — shows env var status without leaking secrets.
    Deploy this, hit /debug, and check the output.
    """
    key = os.environ.get("OPENAI_API_KEY")

    # Check ALL env vars for anything Railway-related (helps confirm
    # Railway is actually injecting vars into this service)
    railway_vars = {k: v[:20] + "..." if len(v) > 20 else v
                    for k, v in os.environ.items()
                    if k.startswith("RAILWAY")}

    # Check if a .env file exists in the working directory
    env_file_exists = os.path.isfile(".env")
    env_file_contents = None
    if env_file_exists:
        try:
            with open(".env", "r") as f:
                # Show key names only, not values
                env_file_contents = [
                    line.split("=")[0].strip()
                    for line in f.readlines()
                    if "=" in line and not line.strip().startswith("#")
                ]
        except Exception as e:
            env_file_contents = f"Error reading: {e}"

    return {
        "openai_key_status": "FOUND" if key else "NOT_FOUND",
        "openai_key_prefix": key[:8] + "..." if key else None,
        "openai_key_length": len(key) if key else 0,
        "railway_detected": bool(RAILWAY_ENV),
        "railway_env_vars": railway_vars,
        "dotenv_file_exists": env_file_exists,
        "dotenv_file_keys": env_file_contents,
        "total_env_var_count": len(os.environ),
    }
