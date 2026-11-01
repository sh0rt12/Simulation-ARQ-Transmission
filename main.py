from src.coding import CRCCalculator
from src.frame import DataFragmenter

# Testowy ciąg znaków
text_data = b"To jest przykladowy ciag danych do przetestowania fragmentacji na ramki w projekcie ARQ!"

# Fragmentator do podziału na kilka ramek - wielkość 25 bajtów
fragmenter = DataFragmenter(chunk_size=25)
frames = fragmenter.fragment(text_data)

# Wybór CRC
crc = CRCCalculator('CRC-32')

print(f"Otrzymano danych: {len(text_data)} bajtow. Podzielono na {len(frames)} ramek.\n")

# Wyświetlanie ramek z parametrami
for frame in frames:
    frame.display_info(crc)