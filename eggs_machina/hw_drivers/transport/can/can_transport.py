from ctypes import *
import time
from types import TracebackType
from typing import Optional, Type

from eggs_machina.hw_drivers.transport.can import PCANBasic
from eggs_machina.hw_drivers.transport.base import Transport
from eggs_machina.hw_drivers.transport.can.types import CAN_Baud_Rate, CAN_Message

class PCAN(Transport):
    def __init__(self, channel: PCANBasic.TPCANHandle, baud_rate: CAN_Baud_Rate):
        self.channel = channel
        self.baud_rate = baud_rate

        self.pcan_baud_rate: PCANBasic.TPCANBaudrate = PCANBasic.PCAN_BAUD_1M
        if baud_rate == CAN_Baud_Rate.CAN_BAUD_125_KBS:
            self.pcan_baud_rate = PCANBasic.PCAN_BAUD_125K
        elif baud_rate == CAN_Baud_Rate.CAN_BAUD_250_KBS:
            self.pcan_baud_rate = PCANBasic.PCAN_BAUD_250K
        elif baud_rate == CAN_Baud_Rate.CAN_BAUD_500_KBS:
            self.pcan_baud_rate = PCANBasic.PCAN_BAUD_500K

    def __enter__(self):
        self.transport = PCANBasic.PCANBasic()
        self.transport.Initialize(self.channel, self.pcan_baud_rate) 

    def __exit__(self, exctype: Optional[Type[BaseException]],
        excinst: Optional[BaseException],
        exctb: Optional[TracebackType]
    ) -> bool:
        self.transport.Uninitialize(self.channel)

    def open(self):
        self.__enter__()
        
    def close(self):
        self.__exit__()

    def recv(self, can_id: int, is_extended_id: bool = False, timeout_s: int = 0.5) -> CAN_Message:
        msg_type = PCANBasic.PCAN_MESSAGE_STANDARD
        if is_extended_id:
            msg_type = PCANBasic.PCAN_MESSAGE_EXTENDED
        end_time = time.time() + timeout_s
        while time.time() < end_time:
            # returns tuple of status, msg, timestamp
            status, msg, _ = self.transport.Read(self.channel)
            if status != PCANBasic.PCAN_ERROR_OK:
                continue
            if int(msg.ID) == can_id and msg.MSGTYPE == msg_type.value:
                return CAN_Message(
                    can_id=int(msg.ID),
                    data_len=int(msg.LEN),
                    data=bytes(msg.DATA)
                )
        return None
    
    def recv_in_range(self, can_id_min: int, can_id_max: int, is_extended_id: bool = False, timeout_s: int = 0.5) -> CAN_Message:
        msg_type = PCANBasic.PCAN_MESSAGE_STANDARD
        if is_extended_id:
            msg_type = PCANBasic.PCAN_MESSAGE_EXTENDED
        end_time = time.time() + timeout_s
        while time.time() < end_time:
            status, msg, _ = self.transport.Read(self.channel)
            if status != PCANBasic.PCAN_ERROR_OK:
                continue
            if int(msg.ID) >= can_id_min and int(msg.ID) <= can_id_max and msg.MSGTYPE == msg_type.value:
                return CAN_Message(
                    can_id=int(msg.ID),
                    data_len=int(msg.LEN),
                    data=bytes(msg.DATA)
                )
        return None
    
    def recv_bitmasked_can_id(self, can_id: int, bitmask: int, is_extended_id: bool, timeout_s: int = 0.5) -> CAN_Message:
        msg_type = PCANBasic.PCAN_MESSAGE_STANDARD
        if is_extended_id:
            msg_type = PCANBasic.PCAN_MESSAGE_EXTENDED
        end_time = time.time() + timeout_s
        while time.time() < end_time:
            status, msg, _ = self.transport.Read(self.channel)
            if status != PCANBasic.PCAN_ERROR_OK:
                continue
            if (msg.ID & bitmask) == (can_id & bitmask) and msg.MSGTYPE == msg_type.value:
                return CAN_Message(
                    can_id=int(msg.ID),
                    data_len=int(msg.LEN),
                    data=bytes(msg.DATA)
                )
        return None
        
    def send(self, can_id: int, data: bytes, is_extended_id: bool = False) -> bool:
        msg = PCANBasic.TPCANMsg()
        msg.ID = can_id
        msg.MSGTYPE = PCANBasic.PCAN_MESSAGE_STANDARD
        if is_extended_id:
            msg.MSGTYPE = PCANBasic.PCAN_MESSAGE_EXTENDED
        msg.LEN = len(data)
        ubyte_data_array = c_ubyte * 8
        msg.DATA = ubyte_data_array(*data)
        try:
            status = self.transport.Write(self.channel, msg)
            if status != PCANBasic.PCAN_ERROR_OK:
                raise
        except:
            print(f"Failed to write CAN-ID: {can_id}")
            return False
        return True    

    def __del__(self):
        self.__exit__()
