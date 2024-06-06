import asyncio
from typing import Dict
import json
from echo_quic import EchoQuicConnection, QuicStreamEvent
import pdu
from datetime import datetime


#Handle user input without blocking the event loop, preventing input() from blocking receipt
async def input_handler(input_queue: asyncio.Queue):
    while True:
        message = await asyncio.to_thread(input, "> ")
        await input_queue.put(message)

#Handle received messages without blocking the event loop
async def receive_messages(conn: EchoQuicConnection, stream_id: int):
    print("[cli] starting receive_messages")
    while True:
        try:
            message: QuicStreamEvent = await conn.receive()
            if message.stream_id == stream_id:
                dgram_resp = pdu.Datagram.from_bytes(message.data)
                print(f"\r{dgram_resp.msg}\n> ", end="", flush=True)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

#Main client function
async def echo_client_proto(scope: Dict, conn: EchoQuicConnection):
    print('[cli] starting client')
    while True:
        print("Please log in to an account.")
        user = input("Username: ")
        password = input("Password: ")
        new_stream_id = conn.new_stream()
        join_msg = pdu.Datagram(pdu.MSG_TYPE_HELLO, int(round(datetime.now().timestamp())), json.dumps({"user": user, "password": password}))
        qs = QuicStreamEvent(new_stream_id, join_msg.to_bytes(), False)
        await conn.send(qs)
        message: QuicStreamEvent = await conn.receive()
        dgram_resp = pdu.Datagram.from_bytes(message.data)
        print(dgram_resp.msg)
        if dgram_resp.mtype == pdu.MSG_TYPE_WELCOME:
            print("Type /exit to log out.")
            input_queue = asyncio.Queue()
            receive_task = asyncio.create_task(receive_messages(conn, new_stream_id))
            send_task = asyncio.create_task(send_messages(conn, new_stream_id, input_queue))
            input_task = asyncio.create_task(input_handler(input_queue))
            await asyncio.sleep(0.1)  # Give the tasks time to start
            break
        else:
            print("Invalid login credentials. Please try again.")

    while True:
        await asyncio.sleep(3)  # Refresh every 3 seconds

#Send messages to the server
async def send_messages(conn: EchoQuicConnection, stream_id: int, input_queue: asyncio.Queue):
    while True:
        message = await input_queue.get()
        if message.lower() == "/exit":
            exit_msg = pdu.Datagram(pdu.MSG_TYPE_EXIT, int(round(datetime.now().timestamp())), "exit")
            qs = QuicStreamEvent(stream_id, exit_msg.to_bytes(), True)  # Set end_stream to True
            await conn.send(qs)
            break
        datagram = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), message)
        qs = QuicStreamEvent(stream_id, datagram.to_bytes(), False)
        await conn.send(qs)

