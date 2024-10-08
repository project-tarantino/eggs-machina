"""The driver for using the USB2CAN-X2 device by innomaker."""

from types import TracebackType
from typing import Optional, Type
from eggs_machina.hw_drivers.transport.base import Transport
import can
import os

from eggs_machina.hw_drivers.transport.can.types import CAN_Message

class USB2CANX2(Transport):
    def __init__(self, channel: str, baud_rate: int):
        os.system(f'sudo ifconfig {channel} down')
        os.system(f'sudo ip link set {channel} type can bitrate {baud_rate}')
        os.system(f"sudo ifconfig {channel} txqueuelen {baud_rate}")
        os.system(f'sudo ifconfig {channel} up')
        self.baud_rate = baud_rate
        self.channel = channel
        self.interface = 'socketcan'
        self.bus = can.interface.Bus(channel=self.channel, interface=self.interface)

    def __enter__(self):
        os.system(f'sudo ifconfig {self.channel} up')
        return self

    def __exit__(self, exctype: Optional[Type[BaseException]],
        excinst: Optional[BaseException],
        exctb: Optional[TracebackType]
    ) -> bool:
        os.system(f'sudo ifconfig {self.channel} down')
        self.bus.shutdown()

    def open(self):
        self.__enter__()

    def close(self): 
        self.__exit__()

    def recv(self, can_id: int, is_extended_id: bool, timeout_s: int = 0.5) -> any:
        msg = self.bus.recv(timeout=timeout_s) 
        if msg:
            if int(msg.arbitration_id) == can_id:
                return CAN_Message(
                    can_id=int(msg.arbitration_id),
                    data_len=int(len(msg.data)),
                    data=bytes(msg.data)
                )
        return None
    
    def recv_in_range(self, can_id_min: int, can_id_max: int, is_extended_id: bool = False, timeout_s: int = 0.5) -> CAN_Message:
        msg = self.bus.recv(timeout=timeout_s) 
        if int(msg.arbitration_id) > can_id_min and int(msg.arbitration_id) < can_id_max:
            return CAN_Message(
                can_id=int(msg.arbitration_id),
                data_len=int(len(msg.data)),
                data=bytes(msg.data)
            )
        return None
    
    def recv_bitmasked_can_id(self, can_id: int, bitmask: int, is_extended_id: bool, timeout_s: int = 0.5) -> CAN_Message:
        msg = self.bus.recv(timeout=timeout_s) 
        if (int(msg.arbitration_id) & bitmask) == (can_id & bitmask):
            return CAN_Message(
                can_id=int(msg.arbitration_id),
                data_len=int(len(msg.data)),
                data=bytes(msg.data)
            )
        return None

    def send(self, can_id: int, data: bytes, is_extended_id: bool, *args, **kwargs) -> bool:
        msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=is_extended_id)
        try:
            self.bus.send(msg)
        except:
            print(f"Failed to write CAN-ID: {can_id}")
            return False
        return True

    # def __del__(self):
    #     self.__exit__()

if __name__ == "__main__":
    usb2can = USB2CANX2(channel="can1", baud_rate=10000)
    usb2can.recv(can_id=12, is_extended_id=True, timeout_s=10)
    # usb2can.send(can_id=1,data=bytes([0, 0, 0, 0, 0, 0, 0, 0]), is_extended_id=True)
    # os.system('sudo ifconfig can1 down')