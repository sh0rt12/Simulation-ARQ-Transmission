import random

class ChannelModel:
    BSC = "BSC"

# Klasa symulująca zakłócenia w kanale
class Channel:

    def __init__(self, model: str = ChannelModel.BSC, p: float = 0.001):
        self.model = model
        self.p = p  # Prawdopodobieństwo błędu dla pojedynczego bitu

    # Przetwarzanie strumienia bajtów przez kanał BSC z zakłóceniami
    def apply_noise(self, data: bytes) -> bytes:
        if not data:
            return data

        corrupted = bytearray(data)

        for byte_idx in range(len(corrupted)):
            byte_val = corrupted[byte_idx]

            for bit_idx in range(8):
                if random.random() < self.p:
                    # Odwrócenie bitu na odpowiedniej pozycji (XOR)
                    byte_val ^= (1 << (7 - bit_idx))

            corrupted[byte_idx] = byte_val

        return bytes(corrupted)