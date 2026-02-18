import logging
import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.security import validate_auth
from core.log_config import setup_logging
from core.config import meta, settings
from core import stats_store
from api.routers import simulator, walker, settings as settings_router, traps, mibs, browser, stats

setup_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — auto-start simulator + trap receiver on boot  (Part A)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: conditionally auto-start simulator and trap receiver."""
    from services.sim_manager import SimulatorManager
    from services.trap_manager import trap_manager
    from api.routers.simulator import set_sim_start_time

    if settings.AUTO_START_SIMULATOR:
        try:
            result = SimulatorManager.start()
            logger.info(f"Auto-start simulator: {result['status']}")
            if result.get("status") == "started":
                set_sim_start_time()             # seed run-seconds tracker
                stats_store.increment("simulator", "start_count")
        except Exception as e:
            logger.error(f"Auto-start simulator failed: {e}")

    if settings.AUTO_START_TRAP_RECEIVER:
        try:
            result = trap_manager.start()
            logger.info(f"Auto-start trap receiver: {result['status']}")
        except Exception as e:
            logger.error(f"Auto-start trap receiver failed: {e}")

    yield  # application runs
    # Graceful shutdown — stop subprocesses so they don't become orphans
    try:
        SimulatorManager.stop()
        logger.info("Shutdown: simulator stopped")
    except Exception:
        pass
    try:
        trap_manager.stop()
        logger.info("Shutdown: trap receiver stopped")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title=meta.NAME, version=meta.VERSION, lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS  (BUG-16: explicit origins, no wildcard + credentials)
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/meta")
def get_app_metadata():
    return {
        "name":        meta.NAME,
        "version":     meta.VERSION,
        "author":      meta.AUTHOR,
        "description": meta.DESCRIPTION,
    }


@app.get("/api/health")
def health_check():
    return {
        "status":  "healthy",
        "service": meta.NAME,
        "version": meta.VERSION,
    }


# ---------------------------------------------------------------------------
# Routers
# NOTE: files.py router intentionally NOT registered — deprecated (Phase 3).
# ---------------------------------------------------------------------------
app.include_router(simulator.router,        prefix="/api", dependencies=[Depends(validate_auth)])
app.include_router(walker.router,           prefix="/api", dependencies=[Depends(validate_auth)])
app.include_router(traps.router,            prefix="/api", dependencies=[Depends(validate_auth)])
app.include_router(browser.router,          prefix="/api", dependencies=[Depends(validate_auth)])
app.include_router(mibs.router,             prefix="/api", dependencies=[Depends(validate_auth)])
app.include_router(stats.router,            prefix="/api", dependencies=[Depends(validate_auth)])
app.include_router(settings_router.router,  prefix="/api")  # public: login lives here


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
