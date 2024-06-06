import os
import asyncio
from datetime import datetime
from typing import Coroutine,Dict
import json
from echo_quic import EchoQuicConnection, QuicStreamEvent
import pdu

onlineUsers = {}

def read_users():
    return json.load(open("users.json", "r"))

def valid_login(username, password):
    userFile = read_users()
    for user in userFile["users"]:
        print(user)
        if user["username"] == username and user["password"] == password:
            return True, user["username"]
    return False, None

async def echo_server_proto(scope:Dict, conn:EchoQuicConnection):
    while True:
        try:
            message:QuicStreamEvent = await conn.receive()
            streamID = message.stream_id

            dgram_in = None
            try:
                dgram_in = pdu.Datagram.from_bytes(message.data)
                print("[svr] received message: ", dgram_in.msg)
            except json.JSONDecodeError:
                print(f"Invalid JSON received: {message.data}")
                continue
            print("Asdas")
            if dgram_in:
                #CHECK MESSAGE TYPE:
                if dgram_in.mtype == pdu.MSG_TYPE_HELLO: # Case: Client Login 
                    payload = json.loads(dgram_in.msg)
                    print(payload)
                    valid, username = valid_login(payload["user"],payload["password"])
                    if valid:
                        onlineUsers[streamID] = {"user":username,"conn":conn}
                        print("Asdas")
                        welcome_out = pdu.Datagram(pdu.MSG_TYPE_WELCOME, int(round(datetime.now().timestamp())), str(f"Successful login. Currently online users: {','.join(user['user'] for user in onlineUsers.values())}"))
                        print("Asdas")
                        await conn.send(QuicStreamEvent(streamID, welcome_out.to_bytes(), False))
                        print("Asdas")
                        join_notif = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), f"{username} has joined the chat.")
                        await sendToClients(streamID, join_notif)
                        print("Asdas")
                    else:
                        error_out = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), "Invalid login credentials")
                        await conn.send(QuicStreamEvent(streamID, error_out.to_bytes(), False))
                elif dgram_in.mtype == pdu.MSG_TYPE_TEXT: # Case: Client Message
                    username = onlineUsers[streamID]["user"] 
                    message_out = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), f"{datetime.now().time()} {username}: {dgram_in.msg}")
                    await sendToClients(streamID, message_out)
                elif dgram_in.mtype == pdu.MSG_TYPE_EXIT: # Case: Client Logout
                    username = onlineUsers[streamID]["user"]
                    exit_notif = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), f"{username} has logged out.")
                    del onlineUsers[streamID]
                    await sendToClients(streamID, exit_notif)
            else:
                print("Invalid message received.")
        except Exception as e:
            raise e
           

async def sendToClients(sender_stream, datagram):
    for streamID, user in onlineUsers.items():
        if streamID != sender_stream:
            await user["conn"].send(QuicStreamEvent(streamID, datagram.to_bytes(), False))