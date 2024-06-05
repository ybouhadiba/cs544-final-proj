
from typing import Dict
import json
import asyncio
from echo_quic import EchoQuicConnection, QuicStreamEvent
import pdu
from datetime import datetime


async def echo_client_proto(scope:Dict, conn:EchoQuicConnection):
    
    #START CLIENT HERE
    print('[cli] starting client')
    #datagram = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp())), 1, "qaosikdpoaskd is a test message")
    while True:
        print("Please log in to an account.")
        user = input("Username: ")
        password = input("Password: ")
        new_stream_id = conn.new_stream()
        join_msg = pdu.Datagram(pdu.MSG_TYPE_HELLO, int(round(datetime.now().timestamp())), json.dumps({"user":user, "password":password}))
        qs = QuicStreamEvent(new_stream_id, join_msg.to_bytes(), False)
        await conn.send(qs)
        message:QuicStreamEvent = await conn.receive()
        dgram_resp = pdu.Datagram.from_bytes(message.data)
        print(dgram_resp.msg)
        if dgram_resp.mtype == pdu.MSG_TYPE_WELCOME:
            print("Type /exit to log out.")
            break
        else:
            print("Invalid login credentials. Please try again.")
    while True:
        message = input("")
        if message.lower() == "/exit":
            exit_msg = pdu.Datagram(pdu.MSG_TYPE_EXIT, int(round(datetime.now().timestamp())), "exit")
            qs = QuicStreamEvent(new_stream_id, exit_msg.to_bytes(), False)
            await conn.send(qs)
            break
        datagram = pdu.Datagram(pdu.MSG_TYPE_TEXT, int(round(datetime.now().timestamp()), message))
        qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
        await conn.send(qs)
        message:QuicStreamEvent = await conn.receive()
        dgram_resp = pdu.Datagram.from_bytes(message.data)
        print(dgram_resp.msg)

        while True:
            try:
                message:QuicStreamEvent = await conn.receive()
                dgram_resp = pdu.Datagram.from_bytes(message.data)
                print(dgram_resp.msg)
            except asyncio.TimeoutError:
                break

#     qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
#     await conn.send(qs)
#     message:QuicStreamEvent = await conn.receive()
#     dgram_resp = pdu.Datagram.from_bytes(message.data)
#     print('[cli] got message: ', dgram_resp.msg)
#     print('[cli] msg as json: ', dgram_resp.to_json())
#     #END CLIENT HERE