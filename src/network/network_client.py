"""
Recoil Wing - Client Network Controller.
Thread-safe, non-blocking WebSocket client that connects the Pygame client
to the Multiplayer Relay Server. Supports both Desktop and Web (WASM).
"""
import os
import sys
import json
import queue
import logging
import threading
import asyncio

IS_WASM = sys.platform == "emscripten" or hasattr(sys, "_emscripten_info")


def get_default_server_url():
    """Detects server URL from environment variable, server_config.json, or fallback."""
    # 1. Environment variable
    env_url = os.environ.get("RECOIL_SERVER_URL")
    if env_url:
        return env_url

    # 2. Local config file (server_config.json in project root)
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), "..", "..", "server_config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
                if "server_url" in cfg and cfg["server_url"]:
                    return cfg["server_url"]
    except Exception:
        pass

    return "ws://127.0.0.1:8765"


class NetworkClient:
    def __init__(self, server_url=None):
        self.server_url = server_url or get_default_server_url()
        self.connected = False
        self.role = None          # 'host' or 'guest'
        self.room_code = None
        self.shared_seed = None
        self.rival_ready = False
        self.rival_alive = True
        self.rival_score = 0
        self.rival_pos = {"x": -100, "y": -100, "vy": 0, "shooting": False}

        # Thread-safe queues for communication between Pygame and WebSocket worker
        self.inbox = queue.Queue()
        self.outbox = queue.Queue()

        self._thread = None
        self._loop = None
        self._ws = None
        self._running = False

    def start(self, server_url=None):
        """Starts background network worker (Thread on Desktop, JS WebSocket on WASM/Web)."""
        if server_url:
            self.server_url = server_url
        if self._running:
            return

        self._running = True
        if IS_WASM:
            self._start_wasm_websocket()
        else:
            self._thread = threading.Thread(target=self._worker_thread, daemon=True)
            self._thread.start()

    def _start_wasm_websocket(self):
        """Initializes browser native WebSocket via Emscripten platform bridge."""
        try:
            from platform import window
            url = self.server_url
            try:
                # Allow query parameter override e.g. ?server=wss://...
                params = window.URLSearchParams.new(window.location.search)
                if params.has("server"):
                    url = params.get("server")
            except Exception:
                pass

            logging.info(f"[WASM NetworkClient] Connecting to {url}...")
            self._ws = window.WebSocket.new(url)

            def on_open(event):
                self.connected = True
                self.inbox.put({"type": "connected", "url": url})
                logging.info("[WASM NetworkClient] Connected successfully!")

            def on_message(event):
                try:
                    data = json.loads(str(event.data))
                    self._handle_incoming_message(data)
                except Exception as e:
                    logging.error(f"[WASM NetworkClient] JSON parse error: {e}")

            def on_error(event):
                self.connected = False
                self.inbox.put({"type": "connection_error", "error": "WebSocket error occurred"})

            def on_close(event):
                self.connected = False
                self.inbox.put({"type": "connection_error", "error": "Connection closed"})

            self._ws.onopen = on_open
            self._ws.onmessage = on_message
            self._ws.onerror = on_error
            self._ws.onclose = on_close
        except Exception as e:
            logging.error(f"[WASM NetworkClient] Failed to setup WebSocket: {e}")

    def stop(self):
        """Stops network client and closes connection."""
        self._running = False
        self.connected = False
        if self.outbox:
            self.outbox.put({"type": "_stop"})

    def _worker_thread(self):
        """Background thread running asyncio event loop for WebSockets."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run_client())
        except Exception as e:
            logging.error(f"[NetworkClient] Worker loop error: {e}")
        finally:
            self._loop.close()

    async def _run_client(self):
        """Main async connection loop."""
        import websockets
        while self._running:
            try:
                logging.info(f"[NetworkClient] Connecting to {self.server_url}...")
                async with websockets.connect(self.server_url) as ws:
                    self._ws = ws
                    self.connected = True
                    self.inbox.put({"type": "connected", "url": self.server_url})
                    logging.info("[NetworkClient] Connected to relay server!")

                    # Run sender and receiver concurrently
                    send_task = asyncio.create_task(self._sender_loop(ws))
                    recv_task = asyncio.create_task(self._receiver_loop(ws))
                    done, pending = await asyncio.wait(
                        [send_task, recv_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()
            except Exception as e:
                self.connected = False
                self.inbox.put({"type": "connection_error", "error": str(e)})
                logging.warning(f"[NetworkClient] Connection error: {e}. Retrying in 3s...")
                await asyncio.sleep(3)

    async def _sender_loop(self, ws):
        """Continuously pulls messages from outbox queue and sends over WS."""
        while self._running:
            try:
                # Check outbox without blocking asyncio loop
                while not self.outbox.empty():
                    msg = self.outbox.get_nowait()
                    if msg.get("type") == "_stop":
                        return
                    await ws.send(json.dumps(msg))
                await asyncio.sleep(0.016)  # ~60 Hz poll
            except Exception as e:
                logging.error(f"[NetworkClient] Send error: {e}")
                break

    async def _receiver_loop(self, ws):
        """Continuously listens for incoming WS messages and puts into inbox."""
        async for raw_message in ws:
            try:
                data = json.loads(raw_message)
                self._handle_incoming_message(data)
            except Exception as e:
                logging.error(f"[NetworkClient] Recv parse error: {e}")

    def _handle_incoming_message(self, data):
        """Internal dispatch of server messages."""
        msg_type = data.get("type")
        if msg_type == "room_created":
            self.room_code = data["room_code"]
            self.role = "host"
            self.shared_seed = data["seed"]
        elif msg_type == "room_joined":
            self.room_code = data["room_code"]
            self.role = "guest"
            self.shared_seed = data["seed"]
        elif msg_type == "rival_joined":
            self.rival_ready = True
        elif msg_type == "start_countdown":
            self.shared_seed = data.get("seed", self.shared_seed)
        elif msg_type == "state":
            self.rival_pos["x"] = data.get("x", self.rival_pos["x"])
            self.rival_pos["y"] = data.get("y", self.rival_pos["y"])
            self.rival_pos["vy"] = data.get("vy", 0)
            self.rival_pos["shooting"] = data.get("shooting", False)
            self.rival_score = data.get("score", self.rival_score)
            self.rival_alive = data.get("alive", True)
        elif msg_type == "crash":
            self.rival_alive = False
        elif msg_type == "rematch_accepted":
            self.shared_seed = data.get("seed")
            self.rival_alive = True

        # Forward to Pygame inbox
        self.inbox.put(data)

    # -------------------------------------------------------------
    # Public API called from Pygame (Main Thread)
    # -------------------------------------------------------------
    def create_room(self):
        """Requests room creation from server."""
        self.outbox.put({"type": "create_room"})

    def join_room(self, room_code):
        """Requests to join an existing room."""
        self.outbox.put({"type": "join_room", "room_code": room_code.upper().strip()})

    def send_ready(self):
        """Informs server this player is ready to race."""
        self.outbox.put({"type": "ready"})

    def send_state(self, x, y, vy, score, alive=True, shooting=False):
        """Sends current player transform and gameplay status."""
        self.outbox.put({
            "type": "state",
            "x": round(x, 1),
            "y": round(y, 1),
            "vy": round(vy, 2),
            "score": score,
            "alive": alive,
            "shooting": shooting,
        })

    def send_crash(self, final_score):
        """Notifies rival and server that player has crashed."""
        self.outbox.put({"type": "crash", "score": final_score})

    def request_rematch(self):
        """Requests a rematch in the current room."""
        self.outbox.put({"type": "rematch"})

    def poll_events(self):
        """
        Pulls all received events from the inbox.
        In WASM mode, also dispatches outbox queue to JS WebSocket.
        Returns a list of event dicts to be handled by Pygame.
        """
        # On WASM, flush outbox messages into native WebSocket
        if IS_WASM and self._ws and self.connected:
            while not self.outbox.empty():
                try:
                    msg = self.outbox.get_nowait()
                    if msg.get("type") != "_stop":
                        self._ws.send(json.dumps(msg))
                except Exception:
                    break

        events = []
        while not self.inbox.empty():
            try:
                events.append(self.inbox.get_nowait())
            except queue.Empty:
                break
        return events
