from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.groups import router as groups_router
from app.api.users import router as users_router
from app.api.workspaces import router as workspaces_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs code at server startup and shutdown — like useEffect with a cleanup.

    The code BEFORE `yield` runs when the server starts.
    The code AFTER `yield` runs when the server shuts down.

    For now this is a placeholder. In later phases we'll add:
    - Database connection pool setup
    - ChromaDB client initialization
    - Embedding model loading
    """
    # --- startup ---
    print(f"Starting {settings.app_name} (debug={settings.debug})")
    yield
    # --- shutdown ---
    print("Shutting down")


app = FastAPI(
    title=settings.app_name,
    # Exposes /docs (Swagger UI) and /redoc — free interactive API documentation
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS middleware lets the React frontend call this API.
# Without this, browsers block cross-origin requests as a security measure.
# In debug mode we allow all origins so the Vite dev server can run on any port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else settings.cors_origins,
    allow_credentials=not settings.debug,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """
    Simple endpoint to verify the server is running.
    The frontend (and Docker health checks) will call this to confirm the
    backend is up before making real requests.
    """
    return {"status": "ok", "app": settings.app_name}


app.include_router(documents_router)
app.include_router(workspaces_router)
app.include_router(users_router)
app.include_router(groups_router)
