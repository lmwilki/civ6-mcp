"""Lightweight HTTP API for the web dashboard.

Provides read-only JSON endpoints for game state. Runs embedded inside the
MCP server process, sharing the same GameConnection via create_app().
"""

import dataclasses
import logging

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from civ_mcp.connection import LuaError
from civ_mcp.game_state import GameState

log = logging.getLogger(__name__)


def create_app(gs: GameState) -> FastAPI:
    """Create a FastAPI app wired to the given GameState."""
    app = FastAPI(
        title="civ6-mcp API",
        description="Read-only game state API for the Civ 6 web dashboard",
    )
    app.state.gs = gs

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3001"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request, exc):
        return JSONResponse(
            status_code=503,
            content={"error": "Game not connected", "detail": str(exc)},
        )

    @app.exception_handler(LuaError)
    async def lua_error_handler(request, exc):
        return JSONResponse(
            status_code=502,
            content={"error": "Lua error", "detail": str(exc)},
        )

    @app.get("/api/overview")
    async def overview(request: Request):
        ov = await request.app.state.gs.get_game_overview()
        return _to_dict(ov)

    @app.get("/api/units")
    async def units(request: Request):
        data = await request.app.state.gs.get_units()
        return _to_dict(data)

    @app.get("/api/cities")
    async def cities(request: Request):
        data = await request.app.state.gs.get_cities()
        return _to_dict(data)

    @app.get("/api/map")
    async def map_area(
        request: Request,
        x: int = Query(..., description="Center X coordinate"),
        y: int = Query(..., description="Center Y coordinate"),
        radius: int = Query(3, ge=1, le=5, description="Radius (1-5)"),
    ):
        tiles = await request.app.state.gs.get_map_area(x, y, radius)
        return _to_dict(tiles)

    @app.get("/api/resources")
    async def resources(request: Request):
        stockpiles, owned, nearby, luxury_count = (
            await request.app.state.gs.get_empire_resources()
        )
        return {
            "stockpiles": _to_dict(stockpiles),
            "owned": _to_dict(owned),
            "nearby": _to_dict(nearby),
            "luxury_count": luxury_count,
        }

    @app.get("/api/tech")
    async def tech(request: Request):
        data = await request.app.state.gs.get_tech_civics()
        return _to_dict(data)

    @app.get("/api/diplomacy")
    async def diplomacy(request: Request):
        data = await request.app.state.gs.get_diplomacy()
        return _to_dict(data)

    return app


def _to_dict(obj):
    """Serialize dataclass instances (including nested) to plain dicts."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, (list, tuple)):
        return [_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    return obj
