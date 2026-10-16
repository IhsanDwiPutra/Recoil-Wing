"""
Recoil Wing - Ultra-Lightweight WebSocket Multiplayer Relay Server.
Handles 1v1 Room creation, deterministic seed sharing, and real-time state relay.
Designed to run locally or deployed for free on Render / Fly.io / Railway / VPS.
"""
import asyncio
import json
import random
import string
import logging
import os
import websockets

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

PORT = int(os.environ.get("PORT", 8765))
HOST = "0.0.0.0"

# Room Store: room_code -> { "host": ws, "guest": ws, "seed": int, "host_ready": bool, "guest_ready": bool }
ROOMS = {}


def is_open(ws):
    """Checks if a websocket connection is active and open."""
    if ws is None:
        return False
    try:
        from websockets.protocol import State
        return ws.state == State.OPEN
    except Exception:
        return not getattr(ws, "closed", True)


def generate_room_code(length=4):
    """Generates a memorable 4-letter uppercase room code."""
    chars = string.ascii_uppercase.replace("O", "").replace("I", "")  # Avoid confusing O/0 and I/1
    for _ in range(100):
        code = "".join(random.choice(chars) for _ in range(length))
        if code not in ROOMS:
            return code
    return "".join(random.choice(chars) for _ in range(length + 1))


async def send_json(ws, data):
    """Safely sends JSON message to a websocket."""
    if not is_open(ws):
        return
    try:
        await ws.send(json.dumps(data))
    except Exception as e:
        logging.warning(f"Failed to send to client: {e}")


async def handle_create_room(ws):
    """Player creates a new match room."""
    room_code = generate_room_code()
    seed = random.randint(100000, 999999)
    ROOMS[room_code] = {
        "host": ws,
        "guest": None,
        "seed": seed,
        "host_ready": False,
        "guest_ready": False,
    }
    logging.info(f"Room created: {room_code} (Seed: {seed})")
    await send_json(ws, {
        "type": "room_created",
        "room_code": room_code,
        "role": "host",
        "seed": seed,
    })
    return room_code, "host"


async def handle_join_room(ws, room_code):
    """Player joins an existing match room."""
    room_code = room_code.upper().strip()
    if room_code not in ROOMS:
        await send_json(ws, {"type": "error", "message": f"Room '{room_code}' not found."})
        return None, None

    room = ROOMS[room_code]
    if is_open(room["guest"]):
        await send_json(ws, {"type": "error", "message": f"Room '{room_code}' is full."})
        return None, None

    room["guest"] = ws
    room["host_ready"] = False
    room["guest_ready"] = False
    logging.info(f"Player joined room: {room_code}")

    # Notify Guest
    await send_json(ws, {
        "type": "room_joined",
        "room_code": room_code,
        "role": "guest",
        "seed": room["seed"],
    })

    # Notify Host
    await send_json(room["host"], {
        "type": "rival_joined",
        "room_code": room_code,
        "message": "Player 2 has joined!",
    })

    return room_code, "guest"


async def handle_ready(room_code, role):
    """Handles players signaling they are ready to launch countdown."""
    if room_code not in ROOMS:
        return
    room = ROOMS[room_code]
    if role == "host":
        room["host_ready"] = True
    elif role == "guest":
        room["guest_ready"] = True

    logging.info(f"Room {room_code} Ready status: host={room['host_ready']}, guest={room['guest_ready']}")

    # If both players are ready, trigger synchronized countdown
    if room["host_ready"] and room["guest_ready"]:
        logging.info(f"Both players ready in room {room_code}. Starting countdown!")
        countdown_msg = {
            "type": "start_countdown",
            "seconds": 3,
            "seed": room["seed"],
        }
        await send_json(room["host"], countdown_msg)
        await send_json(room["guest"], countdown_msg)


async def handle_relay_state(room_code, role, data):
    """Relays real-time position/action data to the rival player."""
    if room_code not in ROOMS:
        return
    room = ROOMS[room_code]
    target_ws = room["guest"] if role == "host" else room["host"]
    if is_open(target_ws):
        data["role"] = role
        await send_json(target_ws, data)


async def handle_rematch(room_code):
    """Resets room seed for a new match with same players."""
    if room_code not in ROOMS:
        return
    room = ROOMS[room_code]
    room["seed"] = random.randint(100000, 999999)
    room["host_ready"] = False
    room["guest_ready"] = False
    msg = {"type": "rematch_accepted", "seed": room["seed"]}
    if is_open(room["host"]):
        await send_json(room["host"], msg)
    if is_open(room["guest"]):
        await send_json(room["guest"], msg)


async def client_handler(ws):
    """Main client connection lifecycle handler."""
    current_room = None
    current_role = None
    logging.info(f"Client connected: {ws.remote_address}")

    try:
        async for message in ws:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "create_room":
                current_room, current_role = await handle_create_room(ws)

            elif msg_type == "join_room":
                code = data.get("room_code", "")
                current_room, current_role = await handle_join_room(ws, code)

            elif msg_type == "ready":
                if current_room and current_role:
                    await handle_ready(current_room, current_role)

            elif msg_type in ("state", "crash", "finish", "chat"):
                if current_room and current_role:
                    await handle_relay_state(current_room, current_role, data)

            elif msg_type == "rematch":
                if current_room:
                    await handle_rematch(current_room)

            elif msg_type == "ping":
                await send_json(ws, {"type": "pong"})

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        logging.info(f"Client disconnected: {ws.remote_address} (Room: {current_room})")
        if current_room and current_room in ROOMS:
            room = ROOMS[current_room]
            rival_ws = room["guest"] if current_role == "host" else room["host"]
            if is_open(rival_ws):
                await send_json(rival_ws, {
                    "type": "rival_disconnected",
                    "message": "Rival disconnected from match.",
                })
            # Clean up room
            del ROOMS[current_room]
            logging.info(f"Room {current_room} closed and cleaned up.")


async def main():
    logging.info(f"==================================================")
    logging.info(f"  RECOIL WING MULTIPLAYER RELAY SERVER ACTIVE!    ")
    logging.info(f"  Listening on ws://{HOST}:{PORT}                 ")
    logging.info(f"==================================================")
    async with websockets.serve(client_handler, HOST, PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
