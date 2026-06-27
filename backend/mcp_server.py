from __future__ import annotations

import json
import sys
import traceback
from typing import Any, Dict, Optional

from backend.app.database import Base, engine
from backend.app.models import *  # noqa: F401,F403 - register SQLAlchemy models before create_all
from backend.app.services.mcp_service import (
    call_mcp_tool,
    list_mcp_resources,
    list_mcp_tools,
    read_mcp_resource,
)


SERVER_INFO = {"name": "interlev-local-mcp", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"


def main() -> None:
    Base.metadata.create_all(bind=engine)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
        except Exception as exc:
            response = _error(None, -32603, str(exc), traceback.format_exc())
        if response is not None:
            _send(response)


def handle_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    try:
        if method == "initialize":
            return _result(
                request_id,
                {
                    "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                    },
                    "serverInfo": SERVER_INFO,
                },
            )
        if method in {"notifications/initialized", "initialized"}:
            return None
        if method == "ping":
            return _result(request_id, {})
        if method == "tools/list":
            return _result(request_id, {"tools": list_mcp_tools()})
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            tool_result = call_mcp_tool(name, arguments)
            return _result(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tool_result, indent=2, default=str),
                        }
                    ],
                    "isError": False,
                },
            )
        if method == "resources/list":
            return _result(request_id, {"resources": list_mcp_resources()})
        if method == "resources/read":
            uri = params.get("uri")
            resource = read_mcp_resource(uri)
            return _result(
                request_id,
                {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(resource, indent=2, default=str),
                        }
                    ]
                },
            )
        if method == "prompts/list":
            return _result(request_id, {"prompts": []})
        return _error(request_id, -32601, f"Method not found: {method}")
    except Exception as exc:
        return _error(request_id, -32000, str(exc), traceback.format_exc())


def _result(request_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(
    request_id: Any,
    code: int,
    message: str,
    debug: Optional[str] = None,
) -> Dict[str, Any]:
    error: Dict[str, Any] = {"code": code, "message": message}
    if debug:
        error["data"] = {"debug": debug}
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _send(message: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, default=str) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
