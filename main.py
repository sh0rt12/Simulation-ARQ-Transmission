import os
import struct
from src.channel import Channel
from src.coding import CRCCalculator
from src.frame import DataFragmenter, Frame, FrameType
from src.receiver import Receiver

filename = "test_10KB.txt"

# 1. Automatyczne wygenerowanie pliku 10 KB
if not os.path.exists(filename):
  with open(filename, "wb") as f:
    pattern = b"Symulacja transmisji ARQ - blok danych testowych. "
    data_content = (pattern * (10240 // len(pattern) + 1))[:10240]
    f.write(data_content)
  print(f"[INFO] Wygenerowano plik testowy z tekstem: {filename}\n")

# 2. Odczyt danych z pliku
with open(filename, "rb") as f:
  text_data = f.read()

# 3. Fragmentator do podziału na ramki
fragmenter = DataFragmenter(chunk_size=255, src_addr=0x01, dst_addr=0x02)
frames = fragmenter.fragment(text_data)

# 4. Wybór CRC (CRC-4, CRC-8, CRC-16, CRC-32)
crc = CRCCalculator("CRC-32")

print(
    f"Otrzymano danych: {len(text_data)} bajtow. Podzielono na"
    f" {len(frames)} ramek.\n"
)

# Wyświetalnie ramek z parametrami - na ten moment zakomentowane
# for frame in frames:
#     frame.display_info(crc)

# Inicjalizacja kanału i odbiornika
channel = Channel(model="BSC", p=0.0005)
receiver = Receiver(crc)


# ==============================================================================
# 1. SYMULACJA STOP-AND-WAIT
# ==============================================================================
def run_stop_and_wait():
  print("\n--- STOP-AND-WAIT ---")

  max_retries = 10
  total_retransmissions = 0
  total_sent = 0

  for frame in frames:
    attempts = 0
    success = False

    while attempts < max_retries and not success:
      attempts += 1
      total_sent += 1

      raw_stream = frame.build_full_frame(crc)
      noisy_stream = channel.apply_noise(raw_stream)

      response_bytes = receiver.receive_frame(noisy_stream)
      noisy_response = channel.apply_noise(response_bytes)

      if (
          crc.verify(noisy_response)
          and len(noisy_response) >= 7
          and noisy_response[0] == Frame.START_FLAG
      ):
        # Typ ramki jest na 4 bajcie
        response_type = noisy_response[3]

        if response_type == FrameType.ACK:
          print(
              f"[Sukces] Ramka {frame.seq_num} odebrana i potwierdzona ACK"
              f" (próba {attempts}/{max_retries})"
          )
          success = True
        else:
          print(
              f"[Błąd] Otrzymano NACK dla ramki {frame.seq_num}. Retransmisja..."
          )
          total_retransmissions += 1
      else:
        print("[Błąd] Ramka zwrotna uszkodzona przez szum. Retransmisja...")
        total_retransmissions += 1

    if not success:
      print(
          f"\n[STOP] Zerwanie połączenia! Ramka {frame.seq_num} nie dotarła po"
          f" {max_retries} próbach."
      )
      return

  print("\n--- PODSUMOWANIE STOP-AND-WAIT ---")
  print(f"Wysłano unikalnych ramek: {len(frames)}")
  print(f"Łącznie wysłano w kanał (z powtórkami): {total_sent}")
  print(f"Liczba retransmisji: {total_retransmissions}")


# ==============================================================================
# 2. SYMULACJA GO-BACK-N (Okno przesuwne o rozmiarze N)
# ==============================================================================
def run_go_back_n(window_size: int = 4):
  print(f"\n--- GO-BACK-N (Rozmiar okna N = {window_size}) ---")
  receiver.reset()

  total_frames = len(frames)
  base = 0  # Indeks pierwszej niepotwierdzonej ramki w oknie (0 -> seq_num 1)
  total_retransmissions = 0
  total_sent = 0
  window_rounds = 0
  max_rounds = total_frames * 20  # Zabezpieczenie przed nieskończoną pętlą

  while base < total_frames and window_rounds < max_rounds:
    window_rounds += 1
    window_end = min(base + window_size, total_frames)
    current_window = frames[base:window_end]

    seq_list = [f.seq_num for f in current_window]
    print(f"[Okno {window_rounds}] Wysyłam serię ramek: {seq_list}")

    # 1. Nadajnik wysyła całe okno N ramek jedna po drugiej bez czekania
    responses = []
    for frame in current_window:
      total_sent += 1
      raw_stream = frame.build_full_frame(crc)
      noisy_stream = channel.apply_noise(raw_stream)

      # Odbiornik przetwarza każdą ramkę w kolejności nadejścia
      resp_bytes = receiver.receive_gbn(noisy_stream)
      noisy_resp = channel.apply_noise(resp_bytes)
      responses.append((frame.seq_num, noisy_resp))

    #2. Nadajnik analizuje odpowiedzi zwrotne dla wysłanego okna
    for sent_seq, noisy_resp in responses:
      if (
          crc.verify(noisy_resp)
          and len(noisy_resp) >= 7
          and noisy_resp[0] == Frame.START_FLAG
      ):
        _, _, _, resp_type, resp_seq, _ = struct.unpack(
            "!BBBBHB", noisy_resp[:7]
        )

        if resp_type == FrameType.ACK:
          # Skumulowany ACK potwierdza wszystkie ramki aż do resp_seq włącznie
          if resp_seq > base:
            base = resp_seq
            print(f"   -> Potwierdzono ACK do ramki {resp_seq} włącznie.")
        else:
          print(
              f"   -> Otrzymano NACK (odbiornik nadal czeka na ramkę {resp_seq})"
          )
      else:
        print(
            f"   -> Odpowiedź dla ramki {sent_seq} uszkodzona przez szum w"
            " kanale!"
        )

    # 3. Jeśli okno nie przesunęło się do końca, liczymy ile ramek trzeba cofnąć i powtórzyć
    if base < window_end:
      lost_count = window_end - base
      total_retransmissions += lost_count
      print(
          f"   [COFNIĘCIE GBN] Wracam do ramki {base + 1}! (Do ponownego"
          f" wysłania: {lost_count} ramek z tego okna)"
      )

  if base < total_frames:
    print("[STOP] Przekroczono maksymalną liczbę rund transmisji!")
    return

  # Weryfikacja czy złożony plik u odbiornika jest identyczny z oryginałem
  reconstructed_data = b"".join(receiver.received_chunks)
  is_identical = reconstructed_data == text_data

  print("\n--- PODSUMOWANIE GO-BACK-N ---")
  print(f"Wysłano unikalnych ramek: {total_frames}")
  print(f"Liczba rund (okien): {window_rounds}")
  print(f"Łącznie wysłano w kanał (z powtórkami): {total_sent}")
  print(f"Liczba retransmisji: {total_retransmissions}")
  print(
      "Plik złożony u odbiornika zgodny z oryginałem:"
      f" {'TAK (100%)' if is_identical else 'NIE'}"
  )


if __name__ == "__main__":
  run_stop_and_wait()
  run_go_back_n(window_size=4)