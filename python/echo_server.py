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
				if user["name"] == username and user["password"] == password:
						return True, user["id"]
		return False, None

# User ID system removed, redundant with username for current implementation
# def valid_id(id):
# 		userFile = read_users()
# 		for user in userFile["users"]:
# 				if user["id"] == id:
# 						return True
# 		return False

async def echo_server_proto(scope:Dict, conn:EchoQuicConnection):
		streamID = conn.new_stream()
		buffer = b""
		while True:
				try:
						message:QuicStreamEvent = await conn.receive()
						buffer+=message.data
						userFile = read_users()
						while True:
							try:
								decoded_data, end_pos = json.JSONDecoder().raw_decode(buffer.decode('utf-8'))
								dgram_in = pdu.Datagram(**decoded_data)
								print("[svr] received message: ", dgram_in.msg)
								#CHECK MESSAGE TYPE:
								if dgram_in.mtype == pdu.MSG_TYPE_HELLO: # Case: Client Login 
									payload = json.loads(dgram_in.msg)
									if valid_login(payload["user"],payload["password"]):
										onlineUsers[streamID] = {"user":payload["user"],"conn":conn}
										welcome_out = pdu.Datagram(pdu.MSG_TYPE_WELCOME, int(round(datetime.now().timestamp())), f"Successful login. Currently online users: {','.join(onlineUsers.keys())}")
										await conn.send(QuicStreamEvent(streamID, welcome_out.to_bytes(), False))
										join_notif = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), f"{payload['user']} has joined the chat.")
										await sendToClients(streamID, join_notif)
								elif dgram_in.mtype == pdu.MSG_TYPE_TEXT: # Case: Client Message
									message_out = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), f"{datetime.now.time} {onlineUsers[streamID].key()}: {dgram_in.msg}")
									await sendToClients(streamID, message_out)
								elif dgram_in.mtype == pdu.MSG_TYPE_EXIT: # Case: Client Logout
									exit_notif = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), f"{payload['user']} has logged out.")
									del onlineUsers[streamID]
									await sendToClients(streamID, exit_notif)
							except Exception as e:
									print(e)
									break
				except Exception as e:
						print(e)
						break

async def sendToClients(sender_stream, datagram):
	for streamID, user in onlineUsers.items():
		if streamID != sender_stream:
			await user["conn"].send(QuicStreamEvent(stream_id, datagram.to_bytes(), False))