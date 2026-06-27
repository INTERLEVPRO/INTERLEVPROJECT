import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.mcp_service import (
    call_mcp_tool,
    list_mcp_resources,
    list_mcp_tools,
    read_mcp_resource,
)


router = APIRouter()


class MCPToolCallRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)


@router.get("/health")
def mcp_health(db: Session = Depends(get_db)):
    return call_mcp_tool("interlev_health", {}, db)


@router.get("/tools")
def get_tools():
    return {"tools": list_mcp_tools()}


@router.post("/tools/{tool_name}")
def run_tool(
    tool_name: str,
    payload: MCPToolCallRequest,
    db: Session = Depends(get_db),
):
    try:
        return {"tool": tool_name, "result": call_mcp_tool(tool_name, payload.arguments, db)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/resources")
def get_resources():
    return {"resources": list_mcp_resources()}


@router.get("/resources/read")
def get_resource(uri: str = Query(...)):
    try:
        return {"uri": uri, "content": read_mcp_resource(uri)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/client-config")
def client_config():
    return {
        "mcpServers": {
            "interlev": {
                "command": r"C:\Users\PC\CU-WITH-CODE\.runtime\python312\python.exe",
                "args": ["-m", "backend.mcp_server"],
                "cwd": r"C:\Users\PC\Desktop\CODEGOOGLE\INTERLEV-AI-Agent",
            }
        }
    }


@router.get("/client-config.json")
def client_config_json():
    return Response(
        content=json.dumps(client_config(), indent=2),
        media_type="application/json",
    )
