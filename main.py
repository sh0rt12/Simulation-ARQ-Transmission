import os
from src.coding import CRCCalculator
from src.frame import DataFragmenter

filename = "test_10KB.txt"

# 1. Automatyczne wygenerowanie pliku 10 KB
if not os.path.exists(filename):
    with open(filename, "wb") as f:
        # Tworzymy powtarzające się zdanie (zapisane jako surowe bajty: przedrostek b"")
        wzor = b"Symulacja transmisji ARQ - blok danych testowych. "
        
        # Powielamy wzór tyle razy, żeby przekroczył 10 KB, a następnie ucinamy DOKŁADNIE do 10240 bajtów
        dane = (wzor * (10240 // len(wzor) + 1))[:10240]
        f.write(dane)
    print(f"[INFO] Wygenerowano plik testowy z tekstem: {filename}\n")

# 2. Odczyt danych z pliku
with open(filename, "rb") as f:
    text_data = f.read()

# 3. Fragmentator do podziału na ramki - wielkość 255 bajtów
# Rozmiar 255 (a nie 256!), bo pole długości w nagłówku ma tylko 1 bajt (max wartość to 255 (czyli 2^8 różnych wartości)).
fragmenter = DataFragmenter(chunk_size=255)
frames = fragmenter.fragment(text_data)

# 4. Wybór CRC
crc = CRCCalculator('CRC-32')

print(f"Otrzymano danych: {len(text_data)} bajtow. Podzielono na {len(frames)} ramek.\n")

# 5. Wyświetlanie ramek z parametrami
for frame in frames:
    frame.display_info(crc)