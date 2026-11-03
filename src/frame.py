import struct # moduł do pakowania danych binarnych
from typing import List # moduł do typowania odpowiedzi
from src.coding import CRCCalculator


# Klasa określa identyfikatory rodzajów ramek w protokole
class FrameType:
    DATA = 1 # Paczka z danymi
    ACK = 2 # Potwierdzenie, że paczka przeszła
    NACK = 3 # Informacja o uszkodzonej paczce

    # Zamiana kodu numerycznego typu ramki na tekst
    @classmethod
    def to_string(cls, val: int) -> str:
        names = {cls.DATA: "DATA", cls.ACK: "ACK", cls.NACK: "NACK"}
        return names.get(val, "UNKNOWN")


# Klasa do konstruowania i pakowania nagłówka.
# Ramka transmisyjna zawiera: nagłówek (6 B): Adres źródłowy, Adres docelowy, Typ, Numer paczki, Długość; Dane ; Sumę kontrolną
class Frame:

    # Format nagłówka: Src (1B), Dst (1B), Type (1B), SeqNum (2B), Length (1B) = 6 B
    HEADER_FORMAT = "!BBBHB"
    HEADER_SIZE = 6

    def __init__(self, frame_type: int, seq_num: int, payload: bytes = b"", src_addr: int = 0x01, dst_addr: int = 0x02):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.frame_type = frame_type
        self.seq_num = seq_num
        self.payload = payload
        self.length = len(payload)

        if self.length > 255:
            raise ValueError("Maksymalny rozmiar payloadu to 255 bajtów!")

    # Kodowanie parametrów nagłówka do postaci binarnej o długości 6 B
    def pack_header(self) -> bytes:
        return struct.pack(
            self.HEADER_FORMAT,
            self.src_addr,
            self.dst_addr,
            self.frame_type,
            self.seq_num,
            self.length
        )

    # Składanie pełnej ramki
    def build_full_frame(self, crc_calculator: CRCCalculator) -> bytes:
        raw_content = self.pack_header() + self.payload
        return crc_calculator.encode(raw_content)

    # Wyświetlanie ramki
    def display_info(self, crc_calculator: CRCCalculator):
        header_bytes = self.pack_header()
        raw_content = header_bytes + self.payload
        crc_val = crc_calculator.calculate(raw_content)
        full_frame = crc_calculator.encode(raw_content)

        print("=" * 60)
        print(f" RAMKA NR {self.seq_num} | Typ: {FrameType.to_string(self.frame_type)} | {self.src_addr} -> {self.dst_addr}")
        print("=" * 60)
        print(
            f" > Nagłówek (6 B)    : {header_bytes.hex(' ')}  [Src={self.src_addr}, Dst={self.dst_addr}, Typ={self.frame_type}, Seq={self.seq_num}, Len={self.length}]")
        print(f" > Dane ({self.length} B) : {self.payload.decode('utf-8', errors='replace')}")
        print(
            f" > Suma {crc_calculator.crc_type} ({crc_calculator.bytes_count} B): 0x{crc_val:0{crc_calculator.bytes_count * 2}X}")
        print(f" > PEŁNY STRUMIEŃ BITY/HEX ({len(full_frame)} B): {full_frame.hex(' ')}")
        print("=" * 60 + "\n")


# Dzielenie ciągu danych na ramki o zadanej wielkości - domyślnie 255 B
class DataFragmenter:

    def __init__(self, chunk_size: int = 255, src_addr: int = 0x01, dst_addr: int = 0x02):
        if chunk_size > 255:
            chunk_size = 255
        self.chunk_size = chunk_size
        self.src_addr = src_addr
        self.dst_addr = dst_addr

    def fragment(self, data: bytes) -> List[Frame]:
        frames = []
        seq_num = 1

        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i + self.chunk_size]
            frame = Frame(
                frame_type=FrameType.DATA,
                seq_num=seq_num,
                payload=chunk,
                src_addr=self.src_addr,
                dst_addr=self.dst_addr
            )
            frames.append(frame)
            seq_num += 1

        return frames