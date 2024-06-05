
import json

MSG_TYPE_HELLO = 0x00
MSG_TYPE_WELCOME = 0x01
MSG_TYPE_JOIN = 0x02
MSG_TYPE_JOINACK = 0x03
MSG_TYPE_LEAVE = 0x04
MSG_TYPE_PRESENCE = 0x05
MSG_TYPE_TYPING = 0x06
MSG_TYPE_STOPTYPING = 0x07
MSG_TYPE_TEXT = 0x08
MSG_TYPE_ACK = 0x09
MSG_TYPE_EXIT = 0x0A

class Datagram:
    def __init__(self, mtype:int, timestamp:int, msg:str, sz:int=0):
        self.mtype = mtype
        self.sz = len(msg)
        self.timestamp = timestamp
        #self.sender_id = sender_id # Removed user ID system due to redundancy
        self.msg = msg
        
    def to_json(self):
        return json.dumps(self.__dict__)    
    
    @staticmethod
    def from_json(json_str):
        return Datagram(**json.loads(json_str))
    
    def to_bytes(self):
        return json.dumps(self.__dict__).encode('utf-8')
    
    @staticmethod
    def from_bytes(json_bytes):
        return Datagram(**json.loads(json_bytes.decode('utf-8')))    