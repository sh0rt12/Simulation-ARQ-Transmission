import csv
from src.coding import CRCCalculator
from src.frame import FrameType, Frame
from src.receiver import Receiver
from src.channel import Channel

def run_monte_carlo_tests():
    print("\n" + "="*75)
    print(" PEŁNY GRID SEARCH - BEZ LIMITU RETRANSMISJI (1000 prób)")
    print("="*75)
    
    p_values = [
        0.00001,  
        0.00005,  
        0.0001,   
        0.0002,   
        0.0003,
        0.0005,   
        0.0008,   
        0.001,    
        0.0012,
        0.0015,   
        0.002,    
        0.003
    ]
    
    crc_types = ['CRC-4', 'CRC-8', 'CRC-16', 'CRC-32']
    
    dummy_payload = b"X" * 255
    test_frame = Frame(FrameType.DATA, 1, dummy_payload)
    num_trials = 1000

    csv_filename = "wyniki_bez_limitu_GE.csv"
    
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(["P (Prawdopodobienstwo bledu)", "Typ CRC", "Wyslano ramek", "Laczne retransmisje", "Zepsute ramki (%)", "Status"])
        
        print(f"{'P (Szum)':<10} | {'CRC':<8} | {'Zepsute ramki':<15} | {'Łączne retransmisje'}")
        print("-" * 75)

        for p in p_values:
            for crc_type in crc_types:
                try:
                    crc = CRCCalculator(crc_type)
                except KeyError:
                    continue
                    
                channel = Channel(model="BSC", p=p)
                receiver = Receiver(crc)
                
                total_retransmissions = 0
                
                for _ in range(num_trials):
                    success = False
                    
                    # BRAK LIMITU 
                    while not success:
                        raw_stream = test_frame.build_full_frame(crc)
                        noisy_stream = channel.apply_noise(raw_stream)
                        response_bytes = receiver.receive_frame(noisy_stream)
                        noisy_response = channel.apply_noise(response_bytes)
                        
                        if crc.verify(noisy_response) and len(noisy_response) >= 6:
                            if noisy_response[2] == FrameType.ACK:
                                success = True
                            else:
                                total_retransmissions += 1
                        else:
                            total_retransmissions += 1
                            
                error_rate = (total_retransmissions / (num_trials + total_retransmissions)) * 100 if total_retransmissions > 0 else 0
                
                # Formatowanie pod polskiego Excela (kropki na przecinki)
                p_pl = str(p).replace('.', ',')
                error_pl = str(round(error_rate, 2)).replace('.', ',')
                
                print(f"{p:<10} | {crc_type:<8} | {error_rate:>5.1f} %        | {total_retransmissions}")
                writer.writerow([p_pl, crc_type, num_trials, total_retransmissions, error_pl, "Sukces"])
            
            print("-" * 75)
            writer.writerow([])

    print(f"\n[GOTOWE] Zapisano do pliku Excela: {csv_filename}")

if __name__ == "__main__":
    run_monte_carlo_tests()