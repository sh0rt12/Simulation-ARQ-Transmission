import struct
from src.coding import CRCCalculator
from src.frame import Frame, FrameType


class Receiver:

  def __init__(self, crc_calculator: CRCCalculator):
    self.crc = crc_calculator
    # Stan potrzebny dla Go-Back-N:
    self.expected_seq_num = 1
    self.received_chunks = []

  def reset(self):
    # Resetuje stan odbiornika przed nową transmisją
    self.expected_seq_num = 1
    self.received_chunks = []

  # --- METODA 1: STOP-AND-WAIT ---
  def receive_frame(self, raw_frame_bytes: bytes) -> bytes:
    # 1. Sprawdzenie flagi startu (min. 7B nagłówka + 1B CRC)
    if len(raw_frame_bytes) < 8 or raw_frame_bytes[0] != Frame.START_FLAG:
      response_frame = Frame(
          FrameType.NACK, 0, b"", src_addr=0x02, dst_addr=0x01
      )
      return response_frame.build_full_frame(self.crc)

    # 2. Weryfikacja sumy kontrolnej
    is_valid = self.crc.verify(raw_frame_bytes)

    # 3. Rozpakowanie 7-bajtowego nagłówka (Flag, Dst, Src, Type, SeqNum, Length)
    try:
      header = raw_frame_bytes[:7]
      _, dst, src, _, seq_num, _ = struct.unpack("!BBBBHB", header)
    except Exception:
      dst, src, seq_num = 0x02, 0x01, 0

    # 4. Zbudowanie ramki zwrotnej (zamiana Dst z Src)
    if is_valid:
      response_frame = Frame(
          FrameType.ACK, seq_num, b"", src_addr=dst, dst_addr=src
      )
    else:
      response_frame = Frame(
          FrameType.NACK, seq_num, b"", src_addr=dst, dst_addr=src
      )

    return response_frame.build_full_frame(self.crc)

  # --- METODA 2: GO-BACK-N (pilnuje kolejności ramek) ---
  def receive_gbn(self, raw_frame_bytes: bytes) -> bytes:
    # 1. Sprawdzenie flagi startu 0x7E i minimalnej długości (7B nagłówka + 1B CRC)
    if len(raw_frame_bytes) < 8 or raw_frame_bytes[0] != Frame.START_FLAG:
      response_frame = Frame(
          FrameType.NACK,
          self.expected_seq_num,
          b"",
          src_addr=0x02,
          dst_addr=0x01,
      )
      return response_frame.build_full_frame(self.crc)

    # 2. Sprawdzenie sumy kontrolnej CRC
    is_valid = self.crc.verify(raw_frame_bytes)

    # 3. Rozpakowanie 7-bajtowego nagłówka
    try:
      header = raw_frame_bytes[:7]
      _, dst, src, _, seq_num, length = struct.unpack("!BBBBHB", header)
    except Exception:
      response_frame = Frame(
          FrameType.NACK,
          self.expected_seq_num,
          b"",
          src_addr=0x02,
          dst_addr=0x01,
      )
      return response_frame.build_full_frame(self.crc)

    # 4. Akceptujemy tylko gdy CRC się zgadza oraz numer ramki to dokładnie expected_seq_num
    if is_valid and seq_num == self.expected_seq_num:
      payload = raw_frame_bytes[7 : 7 + length]
      self.received_chunks.append(payload)
      self.expected_seq_num += 1

      # Odsyłamy skumulowane potwierdzenie ACK dla tej ramki
      response_frame = Frame(
          FrameType.ACK, seq_num, b"", src_addr=dst, dst_addr=src
      )
    else:
      # Ramka uszkodzona LUB przyszła poza kolejnością -> odrzucamy i żądamy expected_seq_num
      response_frame = Frame(
          FrameType.NACK, self.expected_seq_num, b"", src_addr=dst, dst_addr=src
      )

    return response_frame.build_full_frame(self.crc)