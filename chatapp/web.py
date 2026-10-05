"""Browser frontend and WebSocket bridge for ChatApp."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from chatapp.client import ChatClient
from chatapp.protocol import ProtocolError, validate_username

FRONTEND_DIR = Path(__file__).with_name("frontend")


def _next_message(messages: Iterator[str]) -> str | None:
    try:
        return next(messages)
    except StopIteration:
        return None


def create_app(chat_host: str = "127.0.0.1", chat_port: int = 8000) -> FastAPI:
    """Create the browser gateway bound to an existing ChatApp TCP server."""
    app = FastAPI(
        title="ChatApp Web",
        description="Browser gateway for the ChatApp TCP server.",
        version="0.2.0",
        docs_url=None,
        redoc_url=None,
    )
    app.state.chat_host = chat_host
    app.state.chat_port = chat_port
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data:; "
            "style-src 'self'; "
            "script-src 'self'; "
            "font-src 'self'"
        )
        return response

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str | int]:
        return {
            "status": "ok",
            "chat_host": app.state.chat_host,
            "chat_port": app.state.chat_port,
        }

    @app.websocket("/ws")
    async def websocket_gateway(websocket: WebSocket) -> None:
        await websocket.accept()

        try:
            username = validate_username(websocket.query_params.get("name", ""))
        except ProtocolError as exc:
            await websocket.send_json({"type": "error", "message": str(exc)})
            await websocket.close(code=1008)
            return

        client = ChatClient(app.state.chat_host, app.state.chat_port)

        try:
            await asyncio.to_thread(client.connect, username)
        except (OSError, ProtocolError) as exc:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"Unable to reach the chat server: {exc}",
                }
            )
            await websocket.close(code=1011)
            return

        await websocket.send_json({"type": "connected", "name": username})
        messages = client.receive_messages()

        async def backend_to_browser() -> None:
            while True:
                message = await asyncio.to_thread(_next_message, messages)
                if message is None:
                    return
                message_type = "system" if message.startswith("[Server]") else "message"
                await websocket.send_json({"type": message_type, "text": message})

        async def browser_to_backend() -> None:
            while True:
                try:
                    payload = await websocket.receive_json()
                except WebSocketDisconnect:
                    return

                if not isinstance(payload, dict) or payload.get("type") != "message":
                    await websocket.send_json(
                        {"type": "error", "message": "Unsupported WebSocket payload."}
                    )
                    continue

                message = payload.get("text")
                if not isinstance(message, str):
                    await websocket.send_json(
                        {"type": "error", "message": "Message text must be a string."}
                    )
                    continue

                try:
                    await asyncio.to_thread(client.send_message, message)
                except ProtocolError as exc:
                    await websocket.send_json({"type": "error", "message": str(exc)})
                except OSError:
                    return

        backend_task = asyncio.create_task(backend_to_browser())
        browser_task = asyncio.create_task(browser_to_backend())
        tasks = {backend_task, browser_task}

        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            if backend_task in done:
                with suppress(RuntimeError, WebSocketDisconnect):
                    await websocket.send_json(
                        {"type": "disconnected", "message": "Chat server connection closed."}
                    )

            client.close()
            for task in pending:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            client.close()
            with suppress(RuntimeError):
                await websocket.close()

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ChatApp browser gateway")
    parser.add_argument("--host", default="127.0.0.1", help="web interface to bind")
    parser.add_argument("--port", type=int, default=8080, help="web port to bind")
    parser.add_argument("--chat-host", default="127.0.0.1", help="TCP chat server host")
    parser.add_argument("--chat-port", type=int, default=8000, help="TCP chat server port")
    args = parser.parse_args(argv)

    uvicorn.run(
        create_app(args.chat_host, args.chat_port),
        host=args.host,
        port=args.port,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
