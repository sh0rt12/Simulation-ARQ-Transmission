# main.py

import os
from src.coding import CRCCalculator
from src.frame import DataFragmenter, FrameType
from src.receiver import Receiver
from src.channel import Channel

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




print("\n--- STOP-AND-WAIT ---")

# TODO: Wiadomości zwrotne (ACK/NACK)
# Odbiornik teraz od razu prosto informuje nadajnik, czy paczka dotarła (zwraca sam status) - zakładamy że odpowiedź dla nadajnika zawsze dociera bezbłędnie.
# Odbiornik powinien stworzyć prawdziwą ramkę z potwierdzeniem i odesłać ją do nadajnika. Powrotna ramka również musi przejść przez kanał BSC (bez danych, lenght=0, sam nagłówek i crc)

# Inicjalizacja kanału BSC
channel = Channel(model="BSC", p=0.0001)

#Inicjalizacja odbiornika
receiver = Receiver(crc)

max_retries = 10
total_retransmissions = 0

# Pętla przechodząca po kolei przez wszystkie ramki
for frame in frames:
    attempts = 0
    success = False
    
    # Wysyłanie ramki dopóki nie będzie ACK lud do max 10 prób
    while attempts < max_retries and not success:
        attempts += 1
        
        # Budujemy strumień bajtów
        raw_stream = frame.build_full_frame(crc)
        
        # Przepuszczenie przez kanał
        noisy_stream = channel.apply_noise(raw_stream)
        
        # Sprawdzenie ramki przez odbiornik
        response = receiver.receive_frame(noisy_stream)
        
        # Reakcja na ACK / NACK
        if response['status'] == FrameType.ACK:
            print(f"[Sukces] Ramka {frame.seq_num} odebrana poprawnie (próba {attempts}/{max_retries})")
            success = True
        else:
            print(f"[Błąd] Ramka {frame.seq_num} uszkodzona. Retransmisja...")
            total_retransmissions += 1
            
    # Zerwanie połączenia - zabezpieczenie przed nieskończoną petlą
    if not success:
        print(f"\nZerwanie połączenia! Ramka {frame.seq_num} nie dotarła po {max_retries} próbach.")
        break 

print("\n--- PODSUMOWANIE TRANSMISJI ---")
print(f"Wysłano ramek: {len(frames)}")
print(f"Liczba retransmisji: {total_retransmissions}")