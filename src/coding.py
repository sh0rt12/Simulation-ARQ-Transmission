# src/coding.py

# Klasa odpowiedzialna za wyliczanie i weryfikację sum kontrolnych CRC (warianty CRC-4,8,16,32)
class CRCCalculator:

    # dzielnik binarny, bity sumy kontrolnej, wartość początkowa, liczba bajtów gotowej sumy po doklejeniu do ramki
    POLYNOMIALS = {
        'CRC-4': {'poly': 0x03, 'bits': 4, 'init': 0x00, 'bytes': 1},
        'CRC-8': {'poly': 0x07, 'bits': 8, 'init': 0x00, 'bytes': 1},
        'CRC-16': {'poly': 0x1021, 'bits': 16, 'init': 0x0000, 'bytes': 2},
        'CRC-32': {'poly': 0x04C11DB7, 'bits': 32, 'init': 0xFFFFFFFF, 'bytes': 4}
    }

    # Konstruktor klasy z domyślnym trybem CRC-16
    def __init__(self, crc_type: str = 'CRC-16'):
        if crc_type not in self.POLYNOMIALS:
            raise ValueError(f"Nieobsługiwany typ CRC: {crc_type}. Wybierz spośród: {list(self.POLYNOMIALS.keys())}")

        self.crc_type = crc_type
        self.config = self.POLYNOMIALS[crc_type]
        self.poly = self.config['poly']
        self.bits = self.config['bits']
        self.bytes_count = self.config['bytes']
        self.mask = (1 << self.bits) - 1

    # Obliczanie wartości sumy kontrolnej
    def calculate(self, data: bytes) -> int:
        crc = self.config['init']

        for byte in data:
            if self.bits < 8:
                # Dla wielomianów krótszych niż bajt (np. CRC-4):
                # Przetwarzamy starszą i młodszą połówkę bajtu (półbajty)
                for nibble in [(byte >> 4) & 0x0F, byte & 0x0F]:
                    crc ^= nibble
                    for _ in range(4):
                        if crc & (1 << (self.bits - 1)):
                            crc = ((crc << 1) ^ self.poly) & self.mask
                        else:
                            crc = (crc << 1) & self.mask
            else:
                # Dla CRC-8, CRC-16, CRC-32:
                crc ^= (byte << (self.bits - 8))
                for _ in range(8):
                    if crc & (1 << (self.bits - 1)):
                        crc = ((crc << 1) ^ self.poly) & self.mask
                    else:
                        crc = (crc << 1) & self.mask

        return crc & self.mask

    # Zamiana bajtów na liczbę i doklejanie bajtów sumy kontrolnej, w celu otrzymania gotowego do wysyłki strumienia
    def encode(self, data: bytes) -> bytes:
        crc_val = self.calculate(data)
        crc_bytes = crc_val.to_bytes(self.bytes_count, byteorder='big')
        return data + crc_bytes

    # Weryfikacja sumy kontrolnej ramki
    def verify(self, frame_bytes: bytes) -> bool:
        if len(frame_bytes) < self.bytes_count:
            return False

        payload = frame_bytes[:-self.bytes_count]
        received_crc = int.from_bytes(frame_bytes[-self.bytes_count:], byteorder='big')

        return self.calculate(payload) == received_crc