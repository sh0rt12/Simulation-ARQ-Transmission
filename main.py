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
        
        # Przepuszczenie przez kanał do odbiornika
        noisy_stream = channel.apply_noise(raw_stream)
        
        # Odbiornik generuje ramkę zwrotną
        response_bytes = receiver.receive_frame(noisy_stream)
        
        # Przepuszczenie ramki zwrotnej przez kanał do nadajnika
        noisy_response = channel.apply_noise(response_bytes)
        
        # NADAJNIK WERYFIKUJE ODPOWIEDŹ ZWROTNĄ
        # Sprawdzamy, czy ramka zwrotna przeszła poprawnie przez CRC i ma odpowiednią długość
        if crc.verify(noisy_response) and len(noisy_response) >= 6:
            # Odczytujemy typ ramki (3 bajt nagłówka to Typ, czyli indeks 2)
            response_type = noisy_response[2]
            
            if response_type == FrameType.ACK:
                print(f"[Sukces] Ramka {frame.seq_num} odebrana i potwierdzona ACK (próba {attempts}/{max_retries})")
                success = True
            else:
                print(f"[Błąd] Otrzymano NACK dla ramki {frame.seq_num}. Retransmisja...")
                total_retransmissions += 1
        else:
            print(f"[Błąd] Ramka zwrotna uszkodzona przez szum. Retransmisja...")
            total_retransmissions += 1
            
    # Zerwanie połączenia - zabezpieczenie przed nieskończoną petlą
    if not success:
        print(f"\n[STOP] Zerwanie połączenia! Ramka {frame.seq_num} nie dotarła po {max_retries} próbach.")
        break

print("\n--- PODSUMOWANIE TRANSMISJI ---")
print(f"Wysłano ramek: {len(frames)}")
print(f"Liczba retransmisji: {total_retransmissions}")