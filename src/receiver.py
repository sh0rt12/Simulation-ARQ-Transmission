# src/receiver.py

from src.coding import CRCCalculator
from src.frame import FrameType

class Receiver:
    def __init__(self, crc_calculator: CRCCalculator):
        self.crc = crc_calculator

    def receive_frame(self, raw_frame_bytes: bytes) -> dict:
        # 1. Weryfikacja sumy kontrolnej
        is_valid = self.crc.verify(raw_frame_bytes)
        
        if not is_valid:
            return {"status": FrameType.NACK, "message": "Błąd - żądanie retransmisji"}
        
        # 2. Jeśli CRC jest OK, w przyszłości tutaj będziemy rozpakowywać nagłówek,
        # wyciągać numer sekwencyjny i odczytywać payload.
        # Na ten moment po prostu zwracamy sukces.
        
        return {"status": FrameType.ACK, "message": "Ramka poprawna"}