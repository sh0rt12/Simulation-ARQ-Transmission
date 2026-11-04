# src/receiver.py

from src.coding import CRCCalculator
from src.frame import FrameType, Frame

class Receiver:
    def __init__(self, crc_calculator: CRCCalculator):
        self.crc = crc_calculator

    def receive_frame(self, raw_frame_bytes: bytes) -> bytes:
        # 1. Weryfikacja sumy kontrolnej
        is_valid = self.crc.verify(raw_frame_bytes)
        
        # 2. Rozpakowanie nagłówka
        try:
            header = raw_frame_bytes[:6]
            src, dst, _, seq_num, _ = struct.unpack("!BBBHB", header)
        except Exception:
            # W przypadku krytycznego uszkodzenia przypisujemy wartości domyślne (i tak nie będzie takiej sytuacji)
            src, dst, seq_num = 0x01, 0x02, 0
            
        # 3. Zbudowanie ramki zwrotnej (zamiana Dst z Src)
        if is_valid:
            response_frame = Frame(FrameType.ACK, seq_num, b"", src_addr=dst, dst_addr=src)
        else:
            response_frame = Frame(FrameType.NACK, seq_num, b"", src_addr=dst, dst_addr=src)
            
        # Zwracamy pełny ciąg bajtów gotowy do wysłania przez kanał
        return response_frame.build_full_frame(self.crc)