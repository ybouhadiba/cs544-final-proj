import os
import asyncio
from datetime import datetime
from typing import Dict
import json
from echo_quic import EchoQuicConnection, QuicStreamEvent
import pdu

onlineUsers = {}

def read_users():
    return json.load(open("users.json", "r"))

def valid_login(username, password):
    userFile = read_users()
    for user in userFile["users"]:
        if user["username"] == username and user["password"] == password:
            return True, user["username"]
    return False, None


async def echo_server_proto(scope: Dict, conn: EchoQuicConnection):
    streamID = None
    username = None
    while True:
        try:
            message: QuicStreamEvent = await conn.receive()
            streamID = message.stream_id

            if message.end_stream:
                if streamID in onlineUsers:
                    exit_notif = pdu.Datagram(
                        pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())),
                        f"{username} has logged out."
                    )
                    await broadcastMessage(exit_notif, exclude_stream=streamID)
                    del onlineUsers[streamID]
                break

            dgram_in = None
            try:
                dgram_in = pdu.Datagram.from_bytes(message.data)
                print("[svr] received message: ", dgram_in.msg)
            except json.JSONDecodeError:
                print(f"Invalid JSON received: {message.data}")
                continue

            if dgram_in:
                # CHECK MESSAGE TYPE:
                if dgram_in.mtype == pdu.MSG_TYPE_HELLO:  # Case: Client Login
                    payload = json.loads(dgram_in.msg)
                    valid, username = valid_login(payload["user"], payload["password"])
                    if valid:
                        onlineUsers[streamID] = {"user": username, "conn": conn}
                        welcome_out = pdu.Datagram(
                            pdu.MSG_TYPE_WELCOME, int(round(datetime.now().timestamp())),
                            str(f"Successful login. Currently online users: {','.join(user['user'] for user in onlineUsers.values())}")
                        )
                        await conn.send(QuicStreamEvent(streamID, welcome_out.to_bytes(), False))
                        join_notif = pdu.Datagram(
                            pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())),
                            f"{username} has joined the chat."
                        )
                        await broadcastMessage(join_notif, exclude_stream=streamID)
                    else:
                        error_out = pdu.Datagram(
                            pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())),
                            "Invalid login credentials"
                        )
                        await conn.send(QuicStreamEvent(streamID, error_out.to_bytes(), False))
                elif dgram_in.mtype == pdu.MSG_TYPE_TEXT:  # Case: Client Message
                    message_out = pdu.Datagram(
                        pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())),
                        f"{username}: {dgram_in.msg}"
                    )
                    await broadcastMessage(message_out)
                elif dgram_in.mtype == pdu.MSG_TYPE_EXIT:  # Case: Client Logout
                    exit_notif = pdu.Datagram(
                        pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())),
                        f"{username} has logged out."
                    )
                    await broadcastMessage(exit_notif, exclude_stream=streamID)
                    del onlineUsers[streamID]
            else:
                print("Invalid message received.")
        except Exception as e:
            if streamID in onlineUsers:
                del onlineUsers[streamID]
            raise e


async def broadcastMessage(datagram, exclude_stream=None):
    for streamID, user in onlineUsers.items():
            try:
                print(f"[svr] broadcasting message: {datagram.msg} to {user['user']}")
                await user["conn"].send(QuicStreamEvent(streamID, datagram.to_bytes(), False))
            except Exception as e:
                print(f"Error broadcasting to {user['user']}: {e}")