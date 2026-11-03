import os
from src.coding import CRCCalculator
from src.frame import DataFragmenter, FrameType
from src.receiver import Receiver

filename = "test_10KB.txt"

# 1. Automatyczne wygenerowanie pliku 10 KB
if not os.path.exists(filename):
    with open(filename, "wb") as f:
        # Tworzymy powtarzające się zdanie (zapisane jako surowe bajty: przedrostek b"")
        pattern = b"Symulacja transmisji ARQ - blok danych testowych. "

        # Powielamy wzór tyle razy, żeby przekroczył 10 KB, a następnie ucinamy DOKŁADNIE do 10240 bajtów
        data_content = (pattern * (10240 // len(pattern) + 1))[:10240]
        f.write(data_content)
    print(f"[INFO] Wygenerowano plik testowy z tekstem: {filename}\n")

# 2. Odczyt danych z pliku
with open(filename, "rb") as f:
    text_data = f.read()

# 3. Fragmentator do podziału na ramki - wielkość 255 bajtów z adresami stacji A (0x01) -> B (0x02)
fragmenter = DataFragmenter(chunk_size=255, src_addr=0x01, dst_addr=0x02)
frames = fragmenter.fragment(text_data)

# 4. Wybór CRC (np. CRC-32)
crc = CRCCalculator('CRC-32')

print(f"Otrzymano danych: {len(text_data)} bajtow. Podzielono na {len(frames)} ramek.\n")

# 5. Wyświetlanie ramek z parametrami
for frame in frames:
    frame.display_info(crc)

print("\n--- TEST ODBIORNIKA ---")

#Inicjalizacja odbiornika
receiver = Receiver(crc)

# Bierzemy pierwszą ramkę i budujemy jej pełny ciąg bajtów
test_frame = frames[0]
ideal_stream = test_frame.build_full_frame(crc)

# Test 1 - wysyłamy idealny strumień do odbiornika
response_1 = receiver.receive_frame(ideal_stream)
print(f"Test 1 (Idealna ramka): {response_1['message']} -> Status: {FrameType.to_string(response_1['status'])}")

# Test 2 - celowo psujemy strumień i wysyłamy do odbiornika
corrupted_stream = bytearray(ideal_stream)
corrupted_stream[10] ^= 0xFF  # Wymuszamy błąd poprzez odwrócenie bitów w 11. bajcie

response_2 = receiver.receive_frame(corrupted_stream)
print(f"Test 2 (Zepsuta ramka): {response_2['message']} -> Status: {FrameType.to_string(response_2['status'])}")