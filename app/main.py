import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from app.config import CONFIG
from app.fortigate import get_policy_status, set_internet_access

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory state: toggle_id -> bool (True = internet ON)
state: dict[str, bool] = {}

async def sync_state_from_fortigate():
    """Load real policy states from Fortigate on startup."""
    for toggle in CONFIG["toggles"]:
        tid = toggle["id"]
        pid = toggle["policy_id"]
        try:
            internet_on = await get_policy_status(pid)
            state[tid] = internet_on
            logger.info(f"Synced {tid}: internet={'ON' if internet_on else 'OFF'} (policy {pid})")
        except Exception as e:
            logger.warning(f"Could not sync {tid} from Fortigate: {e}. Defaulting to OFF.")
            state[tid] = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    await sync_state_from_fortigate()
    yield

app = FastAPI(title="Fortigate Policy Toggler", lifespan=lifespan)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

class ToggleRequest(BaseModel):
    enabled: bool

@app.get("/")
async def root():
    return FileResponse(str(static_dir / "index.html"))

@app.get("/api/status")
async def get_status():
    toggles = []
    for toggle in CONFIG["toggles"]:
        tid = toggle["id"]
        toggles.append({
            "id": tid,
            "label": toggle["label"],
            "enabled": state.get(tid, False),
            "policy_id": toggle["policy_id"],
        })
    return {"toggles": toggles}

@app.post("/api/toggle/{toggle_id}")
async def set_toggle(toggle_id: str, body: ToggleRequest):
    toggle = next((t for t in CONFIG["toggles"] if t["id"] == toggle_id), None)
    if not toggle:
        raise HTTPException(status_code=404, detail="Toggle not found")
    try:
        await set_internet_access(toggle["policy_id"], body.enabled)
        state[toggle_id] = body.enabled
        logger.info(f"Set {toggle_id} internet={'ON' if body.enabled else 'OFF'}")
        return {"id": toggle_id, "enabled": body.enabled}
    except Exception as e:
        logger.error(f"Fortigate error for {toggle_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Fortigate error: {str(e)}")
