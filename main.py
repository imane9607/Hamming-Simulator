#!/usr/bin/env python3
"""
BLM230 Bilgisayar Mimarisi - Hamming SEC-DED Kod Uygulaması
8, 16 ve 32-bit veri girişlerini işler.
Sadece GUI Arayüzü
"""

import random
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math

class HammingSECDED:
    def __init__(self, k_data_bits):
        """
        Genel bir Hamming SEC-DED kodlayıcı/kod çözücü başlatır.
        k_data_bits: Veri biti sayısı (örneğin, 8, 16, 32).
        """
        if k_data_bits not in [8, 16, 32]:
            raise ValueError("Bu uygulama için veri bitleri 8, 16 veya 32 olmalıdır.")

        self.k = k_data_bits
        
        # SEC için eşlik biti sayısını (p) hesapla
        self.p_sec = 0
        while (2**self.p_sec) < (self.k + self.p_sec + 1):
            self.p_sec += 1
            
        self.num_parity_bits_sec = self.p_sec
        self.num_parity_bits_ded = self.p_sec + 1 # Genel eşlik için 1 ekle
        self.n = self.k + self.num_parity_bits_ded # Kod sözcüğündeki toplam bit sayısı

        # Pozisyonları belirle (1-indeksli)
        # SEC için eşlik bitleri 2'nin kuvvetlerindedir
        self.parity_positions_sec = [2**i for i in range(self.p_sec)]
        
        # Veri biti pozisyonları k + p_sec'e kadar olan diğer tüm pozisyonlardır
        self.data_positions = []
        # current_data_idx = 0 # Burada kesinlikle gerekli değil
        for i in range(1, self.k + self.p_sec + 1):
            if i not in self.parity_positions_sec:
                self.data_positions.append(i)
                # current_data_idx += 1 # Burada kesinlikle gerekli değil
        
        # Genel eşlik biti sonda, n pozisyonunda olacaktır
        self.overall_parity_position = self.n

    def get_code_params_str(self):
        return f"({self.n},{self.k})" # SEC-DED ana başlıkta olduğu için buradan kaldırıldı

    def encode(self, data_bits_list):
        """
        k-bit veriyi Hamming SEC-DED kodu kullanarak kodlar.
        data_bits_list: k bitlik liste [d_msb, ..., d_lsb].
        Dönüş: n-bitlik kod sözcüğü listesi.
        """
        if len(data_bits_list) != self.k:
            raise ValueError(f"Veri tam olarak {self.k} bit olmalıdır.")

        # Kod sözcüğü dizisi (daha kolay matematik için 1-indeksli, bu yüzden boyut n+1)
        codeword = [0] * (self.n + 1)

        # 1. Veri bitlerini pozisyonlarına yerleştir
        # data_bits_list'in [d_k-1, d_k-2, ..., d_0] olduğu varsayılıyor
        # ve self.data_positions artan pozisyon numarasına göre sıralanmıştır
        for i in range(self.k):
            codeword[self.data_positions[i]] = data_bits_list[i]

        # 2. SEC eşlik bitlerini hesapla (P1, P2, P4, P8, ...)
        for i in range(self.p_sec):
            p_pos = self.parity_positions_sec[i]
            xor_sum = 0
            for bit_pos in range(1, self.k + self.p_sec + 1):
                # Eğer p_pos'uncu bit, bit_pos'un ikili gösteriminde ayarlanmışsa
                # (bit_pos >> i) & 1, bit_pos'un i'inci bitinin 1 olup olmadığını kontrol eder
                # bu da p_pos eşlik biti tarafından kapsanan pozisyonları kontrol etmeye karşılık gelir
                if (bit_pos >> i) & 1:
                    if bit_pos != p_pos: # Eşlik bitini henüz kendisiyle XOR'lama
                        xor_sum ^= codeword[bit_pos]
            codeword[p_pos] = xor_sum
            
        # 3. Genel eşlik bitini (P_overall) hesapla
        # Bu, 1'den n-1'e kadar olan tüm bitleri kapsar (yani, k veri biti + p_sec eşlik biti)
        overall_parity_val = 0
        for i in range(1, self.n): # n-1'e kadar, P_overall'ın kendisinden önce
            overall_parity_val ^= codeword[i]
        codeword[self.overall_parity_position] = overall_parity_val
            
        return codeword[1:] # 0-indeksli n bitlik liste döndür

    def _calculate_syndrome_and_overall_parity_status(self, received_codeword_list):
        """
        Kod çözme için dahili yardımcı.
        Dönüş: (sendrom_degeri, genel_eslik_dogru_mu)
        sendrom_degeri: SEC bölümünde hata yoksa 0, aksi takdirde hata pozisyonu.
        genel_eslik_dogru_mu: Genel eşlik eşleşiyorsa True, aksi takdirde False.
        """
        if len(received_codeword_list) != self.n:
            raise ValueError(f"Alınan kod sözcüğü {self.n} bit olmalıdır.")

        # Hesaplamalar için 1-indeksli dizi kullan
        r = [0] + received_codeword_list 
        syndrome_val = 0

        # SEC bölümü için sendromu hesapla (ilk n-1 bit)
        for i in range(self.p_sec):
            p_check_pos = self.parity_positions_sec[i] # Bu 2**i'dir
            xor_sum = 0
            for bit_pos in range(1, self.n): # n-1'e kadar olan bitleri kontrol et (SEC bölümü + veri)
                # Eğer bit_pos'un i'inci biti 1 ise (yani bit_pos P_2^i tarafından kapsanıyorsa)
                if (bit_pos >> i) & 1:
                    xor_sum ^= r[bit_pos]
            if xor_sum != 0: # eğer bu eşlik kontrolü başarısız olursa
                syndrome_val += p_check_pos # Sendroma 2'nin kuvvetini ekle

        # Genel eşliği kontrol et
        # İlk n-1 alınan bitten beklenen genel eşliği hesapla
        calculated_overall_parity_of_first_n_minus_1_bits = 0
        for i in range(1, self.n): # 1'den n-1'e kadar olan bitleri topla
            calculated_overall_parity_of_first_n_minus_1_bits ^= r[i]
        
        # Bu hesaplanan genel eşliği alınan genel eşlik biti r[n] ile karşılaştır
        overall_parity_matches = (calculated_overall_parity_of_first_n_minus_1_bits == r[self.overall_parity_position])
        
        return syndrome_val, overall_parity_matches

    def decode(self, received_codeword_list):
        """
        Alınan n-bitlik kod sözcüğünü çöz ve hataları tespit et/düzelt.
        Dönüş: (duzeltilmis_veri_bitleri, hata_durum_kodu, hata_bilgisi)
        hata_durum_kodu: 0=hata yok, 1=tek hata düzeltildi, 2=çift hata tespit edildi (düzeltilemez), 3=genel eşlik bitindeki hata düzeltildi
        hata_bilgisi: dize mesajı veya hata pozisyonu.
        """
        syndrome_val, overall_parity_matches = self._calculate_syndrome_and_overall_parity_status(received_codeword_list)
        
        corrected_codeword = list(received_codeword_list) # Değiştirilebilir bir kopya oluştur
        error_status_code = -1 
        error_info = ""

        if syndrome_val == 0:
            if overall_parity_matches:
                error_status_code = 0  # Hata yok
                error_info = "Hata tespit edilmedi."
            else: # S=0, P_o başarısız
                error_status_code = 3  # Genel eşlik bitinde hata
                error_info = f"Genel eşlik bitinde tek hata (pozisyon {self.overall_parity_position}, 0-indeksli: {self.overall_parity_position-1}) düzeltildi."
                # Genel eşlik bitini düzelt
                corrected_codeword[self.overall_parity_position - 1] = 1 - corrected_codeword[self.overall_parity_position - 1]
        else: # syndrome_val != 0
            if not overall_parity_matches: # S!=0, P_o başarısız -> veri/SEC_eslik bitlerinde tek hata
                error_status_code = 1 # Veri/SEC_eslik bitlerinde tek hata
                error_position = syndrome_val # Sendrom doğrudan 1-indeksli hata pozisyonunu gösterir
                if 1 <= error_position <= (self.n -1) : # Hata pozisyonunun geçerli olduğundan emin ol (SEC bölümü içinde)
                    error_info = f"Pozisyon {error_position}'de (0-indeksli: {error_position-1}) tek hata düzeltildi."
                    corrected_codeword[error_position - 1] = 1 - corrected_codeword[error_position - 1]
                else: # Mantık doğruysa SEC-DED için ilk n-1 bit için sendromla olmamalı
                    error_status_code = 2 # Veya başka bir düzeltilemez hata durumu
                    error_info = f"Düzeltilemez hata (sendrom {syndrome_val} SEC bölümü için aralık dışında veya P_o yanlışlığı genel P biti dışında hata olduğunu gösteriyor)."
            else: # S!=0, P_o doğru -> çift hata
                error_status_code = 2 # Çift hata tespit edildi
                error_info = f"Çift hata tespit edildi (sendrom {syndrome_val}, genel eşlik TAMAM). Düzeltilemez."
                # Veriye güvenilemez, (potansiyel olarak bozulmuş) alınandan orijinal veri bitlerini döndür
        
        # (Potansiyel olarak) düzeltilmiş kod sözcüğünden veri bitlerini çıkar
        extracted_data_bits = []
        # self.data_positions'a göre çıkarma için 1-indeksli corrected_codeword kullan
        temp_corrected_codeword_1_indexed = [0] + corrected_codeword
        for pos in self.data_positions: # self.data_positions 1-indekslidir
            extracted_data_bits.append(temp_corrected_codeword_1_indexed[pos])
            
        return extracted_data_bits, error_status_code, error_info

    def introduce_single_error(self, codeword_list, position=None):
        """ Pozisyon 1-indekslidir """
        if position is None:
            position = random.randint(1, self.n) # Hata için 1-indeksli pozisyon
        
        if not (1 <= position <= self.n):
            raise ValueError(f"Hata pozisyonu {position} [1, {self.n}] aralığının dışında")

        corrupted = list(codeword_list)
        corrupted[position - 1] = 1 - corrupted[position - 1] # 0-indeksli pozisyondaki biti çevir
        return corrupted, position

    def introduce_double_error(self, codeword_list, pos1=None, pos2=None):
        """ pos1 ve pos2 1-indekslidir """
        if pos1 is None or pos2 is None: # Rastgele farklı pozisyonlar seç
            indices = random.sample(range(self.n), 2) # 0-indeksli indeksler
            p1_idx, p2_idx = indices[0], indices[1]
        else: # pozisyonlar 1-tabanlıdır
            if not (1 <= pos1 <= self.n and 1 <= pos2 <= self.n and pos1 != pos2):
                raise ValueError(f"Hata pozisyonları ({pos1},{pos2}) [1, {self.n}] aralığı için geçersiz veya aynı")
            p1_idx = pos1 - 1
            p2_idx = pos2 - 1

        corrupted = list(codeword_list)
        corrupted[p1_idx] = 1 - corrupted[p1_idx]
        corrupted[p2_idx] = 1 - corrupted[p2_idx]
        return corrupted, (p1_idx + 1, p2_idx + 1) # 1-indeksli pozisyonları döndür


class HammingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BLM230 - Hamming SEC-DED Kod Simülatörü")
        self.root.geometry("850x750") 
        self.root.configure(bg='#f0f0f0')
        
        self.current_data_size = tk.IntVar(value=8)
        self.hamming = HammingSECDED(self.current_data_size.get())
        self.current_encoded = None # Son kodlanan kod sözcüğünü saklamak için
        
        self.setup_ui()
        self.update_for_data_size() 
        
    def setup_ui(self):
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(pady=5, fill='x')

        tk.Label(control_frame, text="Veri Bit Uzunluğunu Seçin:", bg='#f0f0f0', font=('Arial', 10)).pack(side='left', padx=(10,5))
        
        data_size_options = [8, 16, 32]
        self.data_size_selector = ttk.Combobox(control_frame, textvariable=self.current_data_size, 
                                               values=data_size_options, state="readonly", width=5)
        self.data_size_selector.pack(side='left', padx=5)
        self.data_size_selector.bind("<<ComboboxSelected>>", self.on_data_size_change)

        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=5)
        
        self.main_title_label = tk.Label(title_frame, text=f"Hamming {self.hamming.get_code_params_str()} SEC-DED Kod Simülatörü", 
                              font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        self.main_title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="BLM230 Bilgisayar Mimarisi - Proje Ödevi", 
                                 font=('Arial', 10), bg='#f0f0f0', fg='#7f8c8d')
        subtitle_label.pack()
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.encoder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.encoder_frame, text="Kodlayıcı")
        self.setup_encoder_tab()
        
        self.decoder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.decoder_frame, text="Kod Çözücü")
        self.setup_decoder_tab()
        
        self.testing_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.testing_frame, text="Hata Testi")
        self.setup_testing_tab()
        
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Bilgi")
        self.setup_info_tab()

    def on_data_size_change(self, event=None):
        new_size = self.current_data_size.get()
        try:
            self.hamming = HammingSECDED(new_size)
            self.current_encoded = None 
            self.update_for_data_size()
            messagebox.showinfo("Veri Boyutu Değiştirildi", f"Simülatör şimdi {new_size} veri biti için Hamming {self.hamming.get_code_params_str()} SEC-DED kodu kullanacak şekilde yapılandırıldı.")
        except ValueError as e:
            messagebox.showerror("Hata", str(e))
            # İsteğe bağlı olarak varsayılan veya önceki geçerli bir boyuta geri dön
            self.current_data_size.set(self.hamming.k) # Eski k'ye geri dön

    def update_for_data_size(self):
        k = self.hamming.k
        n = self.hamming.n
        
        self.main_title_label.config(text=f"Hamming {self.hamming.get_code_params_str()} SEC-DED Kod Simülatörü")

        self.data_entry_label.config(text=f"{k}-bit veri girin (örneğin, {'10110010'[:k]}):")
        self.data_entry.config(width=max(k + 5, 15)) # Minimum genişliği sağla
        self.data_entry.delete(0, tk.END)
        self.data_entry.insert(0, '1' * k) 
        if hasattr(self, 'codeword_frame_encoder'):
             for widget in self.codeword_frame_encoder.winfo_children(): widget.destroy()
        if hasattr(self, 'encode_result'): self.encode_result.config(state=tk.NORMAL); self.encode_result.delete(1.0, tk.END); self.encode_result.config(state=tk.DISABLED)

        self.received_entry_label.config(text=f"{n}-bit alınan kod sözcüğü girin:")
        self.received_entry.config(width=max(n + 5, 20)) # Minimum genişliği sağla
        self.received_entry.delete(0, tk.END)
        if hasattr(self, 'decode_result'): self.decode_result.config(state=tk.NORMAL); self.decode_result.delete(1.0, tk.END); self.decode_result.config(state=tk.DISABLED)

        self.test_data_entry_label.config(text=f"Test Verisi ({k} bit):")
        self.test_data_entry.config(width=max(k + 5, 15))
        self.test_data_entry.delete(0, tk.END)
        self.test_data_entry.insert(0, '1' * k)
        if hasattr(self, 'test_result'): self.test_result.config(state=tk.NORMAL); self.test_result.delete(1.0, tk.END); self.test_result.config(state=tk.DISABLED)

        self.update_info_tab_text()

    def setup_encoder_tab(self):
        input_frame = ttk.LabelFrame(self.encoder_frame, text="Veri Girişi", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        self.data_entry_label = tk.Label(input_frame, text=f"{self.hamming.k}-bit veri girin:")
        self.data_entry_label.pack(anchor='w')
        
        self.data_entry = tk.Entry(input_frame, font=('Courier', 12))
        self.data_entry.pack(pady=5, fill='x', expand=True)
        
        button_frame = tk.Frame(input_frame)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Kodla", command=self.encode_data, bg='#3498db', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(button_frame, text="Temizle", command=lambda: self.data_entry.delete(0, 'end'), bg='#95a5a6', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        output_frame = ttk.LabelFrame(self.encoder_frame, text="Kodlanmış Sonuç", padding=10)
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.codeword_frame_encoder = tk.Frame(output_frame) 
        self.codeword_frame_encoder.pack(pady=10, fill='x')
        
        self.encode_result = scrolledtext.ScrolledText(output_frame, height=10, width=80, font=('Courier', 10), wrap=tk.WORD, state=tk.DISABLED)
        self.encode_result.pack(fill='both', expand=True)
    
    def setup_decoder_tab(self):
        input_frame = ttk.LabelFrame(self.decoder_frame, text="Alınan Kod Sözcüğü", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        self.received_entry_label = tk.Label(input_frame, text=f"{self.hamming.n}-bit alınan kod sözcüğü girin:")
        self.received_entry_label.pack(anchor='w')
        
        self.received_entry = tk.Entry(input_frame, font=('Courier', 12))
        self.received_entry.pack(pady=5, fill='x', expand=True)
        
        button_frame = tk.Frame(input_frame)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Kodu Çöz", command=self.decode_data, bg='#e74c3c', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(button_frame, text="Son Kodlananı Kullan", command=self.use_last_encoded, bg='#f39c12', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        output_frame = ttk.LabelFrame(self.decoder_frame, text="Kod Çözme Sonucu", padding=10)
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.decode_result = scrolledtext.ScrolledText(output_frame, height=15, width=80, font=('Courier', 10), wrap=tk.WORD, state=tk.DISABLED)
        self.decode_result.pack(fill='both', expand=True)

    def setup_testing_tab(self):
        control_frame = ttk.LabelFrame(self.testing_frame, text="Hata Testi Kontrolleri", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.test_data_entry_label = tk.Label(control_frame, text=f"Test Verisi ({self.hamming.k} bit):")
        self.test_data_entry_label.pack(anchor='w')
        self.test_data_entry = tk.Entry(control_frame, font=('Courier', 12))
        self.test_data_entry.pack(pady=2, fill='x', expand=True)
        
        button_frame = tk.Frame(control_frame)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Hatasız Test Et", command=self.test_no_errors, bg='#27ae60', fg='white', font=('Arial', 9)).pack(side='left', padx=3)
        tk.Button(button_frame, text="Tek Hata Test Et", command=self.test_single_error, bg='#e67e22', fg='white', font=('Arial', 9)).pack(side='left', padx=3)
        tk.Button(button_frame, text="Çift Hata Test Et", command=self.test_double_error, bg='#c0392b', fg='white', font=('Arial', 9)).pack(side='left', padx=3)
        tk.Button(button_frame, text="Tüm Durumları Test Et", command=self.test_all_cases, bg='#8e44ad', fg='white', font=('Arial', 9)).pack(side='left', padx=3)
        
        results_frame = ttk.LabelFrame(self.testing_frame, text="Test Sonuçları", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.test_result = scrolledtext.ScrolledText(results_frame, height=15, width=80, font=('Courier', 10), wrap=tk.WORD, state=tk.DISABLED)
        self.test_result.pack(fill='both', expand=True)

    def update_info_tab_text(self):
        k = self.hamming.k
        n = self.hamming.n
        p_sec = self.hamming.num_parity_bits_sec
        p_ded = self.hamming.num_parity_bits_ded

        info_text = f"""
BLM230 Bilgisayar Mimarisi - Hamming SEC-DED Kod Uygulaması

MEVCUT YAPILANDIRMA:
Veri bitleri (k): {k}
SEC Eşlik bitleri (p_sec): {p_sec}
Genel DED Eşlik biti: 1
Toplam Eşlik bitleri (p_ded = p_sec + 1): {p_ded}
Toplam Kod Sözcüğü bitleri (n = k + p_ded): {n}
Kod Türü: Hamming ({n},{k}) SEC-DED (Genişletilmiş Hamming Kodu)

HAMMING SEC-DED KODLARI HAKKINDA:
• Tek Hata Düzelten (SEC): Tek bitlik hataları tespit edip düzeltebilir.
• Çift Hata Tespit Eden (DED): Çift bitlik hataları tespit edebilir (ancak düzeltemez).
  Bu, standart bir Hamming SEC koduna genel bir eşlik biti eklenerek elde edilir.

BİT POZİSYONLARI (1-indeksli, kod sözcüğü için soldan sağa MSB'den LSB'ye konsepti):
• SEC Eşlik bitleri (Ps): 2'nin kuvvetleri olan pozisyonlarda (örneğin, 1, 2, 4, ..., 2^({p_sec-1})).
  Bunlar belirli veri ve diğer eşlik bitleri üzerinden hesaplanır.
• Veri bitleri (D): k + p_sec'e kadar olan kalan pozisyonlar.
• Genel DED Eşlik biti (Po): Pozisyon {n} (son bit). Kendinden önceki tüm {n-1} bit için eşlik sağlar.

HATA TESPİT/DÜZELTME MANTIĞI (S = SEC Sendromu, P_o_durumu = Genel Eşlik Kontrolü):
1. İlk {n-1} biti (veri + SEC eşlik bitleri) kullanarak SEC sendromunu (S) hesaplayın.
2. İlk {n-1} bitin beklenen eşliğini alınan genel eşlik biti ({n}. bit) ile karşılaştırarak genel eşlik durumunu (P_o_durumu) kontrol edin.

   - Eğer S=0 ve P_o_durumu doğruysa: Hata yok.
   - Eğer S!=0 ve P_o_durumu yanlışsa: İlk {n-1} bit içinde S pozisyonunda (1-indeksli) tek hata. Düzeltilebilir.
   - Eğer S!=0 ve P_o_durumu doğruysa: Çift hata tespit edildi. Bu kodla düzeltilemez.
   - Eğer S=0 ve P_o_durumu yanlışsa: Genel eşlik bitinde (Po, {n} pozisyonunda) tek hata. Düzeltilebilir.

NASIL KULLANILIR:
1. Üst kısımdan Veri Bit Uzunluğunu (8, 16 veya 32) seçin. Simülatör ayarlanacaktır.
2. KODLAYICI SEKMESİ: {k}-bit veri (ikili dize) girin ve "Kodla"ya tıklayın. {n}-bitlik kod sözcüğü ve ayrıntılar görüntülenecektir.
3. KOD ÇÖZÜCÜ SEKMESİ: {n}-bitlik alınan bir kod sözcüğü (ikili dize) girin ve "Kodu Çöz"e tıklayın. Sonuç sendromu, hata durumunu ve çözülmüş veriyi gösterecektir.
   Son oluşturulan kod sözcüğünü hızlıca yüklemek için "Son Kodlananı Kullan"ı kullanın.
4. HATA TESTİ SEKMESİ: {k}-bit test verisi girin. Simüle etmek için düğmelere tıklayın:
   - Hata yok.
   - Kod sözcüğünde rastgele tek bitlik bir hata.
   - Kod sözcüğünde rastgele çift bitlik bir hata.
   - Yukarıdaki tüm senaryolar.
   Sonuçlar, hataların SEC-DED tarafından beklendiği gibi işlenip işlenmediğini gösterecektir.

Bu uygulama, gerektiği gibi 8, 16 ve 32-bit veri girişlerini destekler.
Kod parametreleri seçiminize göre dinamik olarak ayarlanır.
Kod sözcüğünün görsel gösterimi, yapısını anlamanıza yardımcı olur.
        """
        if hasattr(self, 'info_scroll'):
            self.info_scroll.config(state=tk.NORMAL)
            self.info_scroll.delete(1.0, tk.END)
            self.info_scroll.insert(tk.END, info_text)
            self.info_scroll.config(state=tk.DISABLED)

    def setup_info_tab(self):
        self.info_scroll = scrolledtext.ScrolledText(self.info_frame, wrap=tk.WORD,
                                                font=('Courier', 9), bg='white', fg='#2c3e50',
                                                padx=10, pady=10, state=tk.DISABLED)
        self.info_scroll.pack(fill='both', expand=True, padx=10, pady=10)
        self.update_info_tab_text() 


    def _display_text_result(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(1.0, text)
        widget.config(state=tk.DISABLED)

    def encode_data(self):
        try:
            data_str = self.data_entry.get().strip()
            if len(data_str) != self.hamming.k or not all(c in '01' for c in data_str):
                messagebox.showerror("Giriş Hatası", f"Lütfen tam olarak {self.hamming.k} bit (0 ve 1) girin.")
                return
            
            data_bits_list = [int(c) for c in data_str]
            encoded_list = self.hamming.encode(data_bits_list)
            self.current_encoded = list(encoded_list) # "Son Kodlananı Kullan" için sakla
            
            for widget in self.codeword_frame_encoder.winfo_children(): widget.destroy()
            self.create_codeword_display(self.codeword_frame_encoder, encoded_list, f"Kodlanmış Hamming {self.hamming.get_code_params_str()} SEC-DED Kod Sözcüğü ({self.hamming.n} bit)")
            
            encoded_str = "".join(map(str, encoded_list))
            result_text = f"{self.hamming.k}-bit veri için KODLAMA SONUCU:\n"
            result_text += f"Giriş verisi ({self.hamming.k} bit): {data_str}\n"
            try:
                 result_text += f"Girişin onluk değeri: {int(data_str, 2)}\n\n"
            except ValueError:
                 result_text += "Girişin onluk değeri: Yok (boş dize veya geçersiz format)\n\n"

            result_text += f"Kodlanmış kod sözcüğü ({self.hamming.n} bit): {encoded_str}\n\n"
            result_text += f"Bit Türü Açıklaması: Ps=SEC Eşlik, D=Veri, Po=Genel Eşlik\n"
            result_text += f"SEC Eşlik Pozisyonları (1-indeksli): {self.hamming.parity_positions_sec}\n"
            result_text += f"Veri Pozisyonları (1-indeksli): {self.hamming.data_positions}\n" # Bunlar giriş verisinden sırayla doldurulur
            result_text += f"Genel DED Eşlik Pozisyonu (1-indeksli): {self.hamming.overall_parity_position}\n"

            self._display_text_result(self.encode_result, result_text)
            
        except Exception as e:
            messagebox.showerror("Kodlama Hatası", f"Kodlama başarısız: {str(e)}")
            self._display_text_result(self.encode_result, f"Hata: {str(e)}")
    
    def decode_data(self):
        try:
            received_str = self.received_entry.get().strip()
            if len(received_str) != self.hamming.n or not all(c in '01' for c in received_str):
                messagebox.showerror("Giriş Hatası", f"Lütfen tam olarak {self.hamming.n} bit (0 ve 1) girin.")
                return
            
            received_list = [int(c) for c in received_str]
            decoded_data_list, status_code, error_info_msg = self.hamming.decode(list(received_list)) # Bir kopya ilet
            
            # Görüntüleme amacıyla, sendromu ve genel eşlik durumunu tekrar al
            syndrome_val, overall_parity_ok = self.hamming._calculate_syndrome_and_overall_parity_status(list(received_list))

            status_messages = { # Bu sözlük doğrudan kullanılmıyor, error_info_msg daha açıklayıcı
                0: "Hata tespit edilmedi.",
                1: "Tek hata düzeltildi.", 
                2: "Çift hata tespit edildi (düzeltilemez).", 
                3: "Genel eşlik bitindeki hata düzeltildi."
            }
            
            decoded_data_str = "".join(map(str, decoded_data_list))
            result_text = f"{self.hamming.n}-bit alınan kod sözcüğü için KOD ÇÖZME SONUCU:\n"
            result_text += f"Alınan kod sözcüğü: {received_str}\n\n"
            result_text += f"SEC Sendrom değeri (S): {syndrome_val} (ikili: {syndrome_val:0{self.hamming.p_sec}b})\n"
            result_text += f"Genel Eşlik Durumu (P_o_durumu): {'Doğru' if overall_parity_ok else 'Yanlış'}\n"
            result_text += f"Durum Kodu: {status_code}\n"
            result_text += f"Yorum: {error_info_msg}\n\n" # decode() fonksiyonundan gelen error_info_msg daha açıklayıcı
            
            result_text += f"Çözülmüş Veri ({self.hamming.k} bit): {decoded_data_str}\n"
            if decoded_data_str:
                 try:
                     result_text += f"Çözülmüş verinin onluk değeri: {int(decoded_data_str, 2)}\n"
                 except ValueError:
                     result_text += "Çözülmüş verinin onluk değeri: Yok\n"
            else:
                result_text += "Veri çıkarılamadı (muhtemelen düzeltilemez hata durumu veya boş liste nedeniyle).\n"

            self._display_text_result(self.decode_result, result_text)
            
        except Exception as e:
            messagebox.showerror("Kod Çözme Hatası", f"Kod çözme başarısız: {str(e)}")
            self._display_text_result(self.decode_result, f"Hata: {str(e)}")

    def use_last_encoded(self):
        if self.current_encoded:
            encoded_str = ''.join(map(str, self.current_encoded))
            self.received_entry.delete(0, tk.END)
            self.received_entry.insert(0, encoded_str)
            messagebox.showinfo("Yükleme Başarılı", "Son kodlanan kod sözcüğü kod çözücü girişine yüklendi.")
        else:
            messagebox.showwarning("Veri Yok", "Kullanılabilir kodlanmış veri yok. Lütfen önce Kodlayıcı sekmesinde veri kodlayın.")
    
    def test_no_errors(self): self.run_test_scenario("no_error")
    def test_single_error(self): self.run_test_scenario("single_error")
    def test_double_error(self): self.run_test_scenario("double_error")
    def test_all_cases(self): self.run_test_scenario("all")
    
    def run_test_scenario(self, scenario):
        try:
            data_str = self.test_data_entry.get().strip()
            if len(data_str) != self.hamming.k or not all(c in '01' for c in data_str):
                messagebox.showerror("Giriş Hatası", f"Lütfen test verisi için tam olarak {self.hamming.k} bit (0 ve 1) girin.")
                return
            
            data_bits_orig = [int(c) for c in data_str]
            encoded_orig = self.hamming.encode(list(data_bits_orig))
            
            result_text = f"Hamming {self.hamming.get_code_params_str()} SEC-DED için HATA TESTİ SONUÇLARI\n"
            result_text += f"{'='*70}\n"
            result_text += f"Orijinal Test Verisi ({self.hamming.k} bit): {data_str}\n"
            result_text += f"Kodlanmış Kod Sözcüğü ({self.hamming.n} bit): {''.join(map(str,encoded_orig))}\n\n"
            
            all_tests_passed = True

            if scenario in ["no_error", "all"]:
                result_text += "TEST 1: Hata Yok\n" + "-"*40 + "\n"
                decoded_data, status, info = self.hamming.decode(list(encoded_orig))
                is_pass = (status == 0 and decoded_data == data_bits_orig)
                if not is_pass: all_tests_passed = False
                result_text += f"  Kod Çözücü Bilgisi: {info}\n"
                result_text += f"  Durum: {status} -> {'BAŞARILI (Hata Tespit Edilmedi, Veri TAMAM)' if is_pass else 'BAŞARISIZ'}\n"
                result_text += f"  Veri Eşleşmesi: {'EVET' if decoded_data == data_bits_orig else 'HAYIR'}\n\n"
            
            if scenario in ["single_error", "all"]:
                result_text += "TEST 2: Tek Hata (rastgele pozisyon)\n" + "-"*40 + "\n"
                corrupted_cw, actual_err_pos = self.hamming.introduce_single_error(list(encoded_orig))
                decoded_data, status, info = self.hamming.decode(list(corrupted_cw))
                # Tek hata durum 1 (veri/sec_eşlikte düzeltildi) veya 3 (genel_eşlikte düzeltildi) olmalıdır
                is_pass = ((status == 1 or status == 3) and decoded_data == data_bits_orig)
                if not is_pass: all_tests_passed = False
                result_text += f"  Hata eklenen 1-indeksli poz: {actual_err_pos}\n"
                result_text += f"  Bozuk KS: {''.join(map(str,corrupted_cw))}\n"
                result_text += f"  Kod Çözücü Bilgisi: {info}\n"
                result_text += f"  Durum: {status} -> {'BAŞARILI (Düzeltildi, Veri TAMAM)' if is_pass else 'BAŞARISIZ'}\n"
                result_text += f"  Veri Eşleşmesi: {'EVET' if decoded_data == data_bits_orig else 'HAYIR'}\n\n"
            
            if scenario in ["double_error", "all"]:
                result_text += "TEST 3: Çift Hata (rastgele pozisyonlar)\n" + "-"*40 + "\n"
                # n'nin çift hata için yeterince büyük olduğundan emin ol
                if self.hamming.n < 2:
                    result_text += "  Atlandı: Kod sözcüğü uzunluğu çift hata için çok kısa.\n\n"
                else:
                    corrupted_cw, (p1, p2) = self.hamming.introduce_double_error(list(encoded_orig))
                    decoded_data, status, info = self.hamming.decode(list(corrupted_cw))
                    # Çift hata durum 2 (tespit edildi, düzeltilemez) olmalıdır. Veri muhtemelen eşleşmeyecektir.
                    is_pass = (status == 2) 
                    if not is_pass: all_tests_passed = False
                    result_text += f"  Hata eklenen 1-indeksli poz: {p1}, {p2}\n"
                    result_text += f"  Bozuk KS: {''.join(map(str,corrupted_cw))}\n"
                    result_text += f"  Kod Çözücü Bilgisi: {info}\n"
                    result_text += f"  Durum: {status} -> {'BAŞARILI (Düzeltilemez Olarak Tespit Edildi)' if is_pass else 'BAŞARISIZ (Gözden Kaçırıldı veya Yanlış Düzeltildi)'}\n"
                    result_text += f"  Veri Eşleşmesi: {'HAYIR (düzeltilemez çift hata için bekleniyor)' if decoded_data != data_bits_orig and status==2 else ('HAYIR (beklenmedik)' if decoded_data != data_bits_orig else 'EVET (beklenmedik, SEC-DED için tek veya hiç hata gibi görünen belirli bir çift hata olabilir)')}\n\n"

            result_text += "="*70 + "\n"
            if scenario == "all":
                result_text += f"Genel Test Sonucu: {'TÜM SENARYOLAR BAŞARILI' if all_tests_passed else 'BİR VEYA DAHA FAZLA SENARYO BAŞARISIZ OLDU'}\n"
            else:
                 result_text += "Belirli test senaryosu tamamlandı.\n"
            self._display_text_result(self.test_result, result_text)
            
        except Exception as e:
            messagebox.showerror("Test Hatası", f"Test başarısız: {str(e)}")
            self._display_text_result(self.test_result, f"Hata: {str(e)}")

    def create_codeword_display(self, parent_frame, codeword_list, title_text):
        # Önceki içeriği temizle
        for widget in parent_frame.winfo_children():
            widget.destroy()

        n_bits = len(codeword_list)
        
        title_label = tk.Label(parent_frame, text=title_text, font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0,5))
        
        # Kanvas ve kaydırma çubuğunu tutacak çerçeve
        display_container = tk.Frame(parent_frame)
        display_container.pack(fill="x", expand=False)

        canvas = tk.Canvas(display_container, height=80) # 3 satır + dolgu için sabit yükseklik
        scrollbar = tk.Scrollbar(display_container, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas) # Bu çerçeve ızgarayı içerecektir

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)

        # scrollable_frame için içerik (grid_display_frame)
        grid_display_frame = tk.Frame(scrollable_frame) # Bu iç çerçeve için özel bir arka plan yok
        grid_display_frame.pack()

        sec_parity_pos = self.hamming.parity_positions_sec
        data_pos = self.hamming.data_positions
        overall_parity_pos = self.hamming.overall_parity_position

        common_label_font = ('Courier', 8)
        bit_value_font = ('Courier', 10, 'bold')
        cell_width = 2 # Potansiyel olarak daha küçük yazı tipi için ayarlandı

        # Satır 0: Pozisyon numaraları (1-indeksli)
        tk.Label(grid_display_frame, text="Poz:", font=(common_label_font[0], common_label_font[1], 'bold')).grid(row=0, column=0, padx=2, pady=1, sticky='e')
        for i in range(1, n_bits + 1):
            tk.Label(grid_display_frame, text=str(i), font=common_label_font, width=cell_width, relief='solid', borderwidth=1).grid(row=0, column=i, padx=0, pady=1, sticky='ew')
        
        # Satır 1: Bit türleri (Ps/D/Po)
        tk.Label(grid_display_frame, text="Tür:", font=(common_label_font[0], common_label_font[1], 'bold')).grid(row=1, column=0, padx=2, pady=1, sticky='e')
        for i in range(1, n_bits + 1): # 1-indeksli pozisyon
            bit_type_str = ""
            color = "white"
            if i == overall_parity_pos:
                bit_type_str = "Po" 
                color = '#FFB6C1' # Açık Pembe
            elif i in sec_parity_pos:
                bit_type_str = "Ps" 
                color = '#FFFACD' # Limon Şifon (daha açık sarı)
            elif i in data_pos:
                bit_type_str = "D"  
                color = '#90EE90' # Açık Yeşil
            
            tk.Label(grid_display_frame, text=bit_type_str, font=(common_label_font[0], common_label_font[1], 'bold'), width=cell_width, bg=color, relief='solid', borderwidth=1).grid(row=1, column=i, padx=0, pady=1, sticky='ew')
        
        # Satır 2: Bit değerleri
        tk.Label(grid_display_frame, text="Değ:", font=(common_label_font[0], common_label_font[1], 'bold')).grid(row=2, column=0, padx=2, pady=1, sticky='e')
        for i, bit_val in enumerate(codeword_list): # i burada 0-indekslidir
            pos_1_indexed = i + 1
            color = "white" 
            if pos_1_indexed == overall_parity_pos: color = '#FFE4E1' # Puslu Gül (çok açık pembe)
            elif pos_1_indexed in sec_parity_pos: color = '#FFFFE0' # Açık Sarı
            elif pos_1_indexed in data_pos: color = '#E0FFE0' # Hanımeli (çok açık yeşil)

            tk.Label(grid_display_frame, text=str(bit_val), font=bit_value_font, width=cell_width, bg=color, relief='solid', borderwidth=1).grid(row=2, column=pos_1_indexed, padx=0, pady=1, sticky='ew')

        # Kanvas ve kaydırma çubuğunu paketle
        canvas.pack(side="top", fill="x", expand=False) # Kanvas dikey olarak genişlememeli
        scrollbar.pack(side="bottom", fill="x")
        
        # Paketlemeden sonra kanvas boyutunu güncelle
        parent_frame.update_idletasks() # Tüm widget'ların yerleştirildiğinden emin ol
        canvas.config(scrollregion=canvas.bbox("all"))
        # Kanvas yüksekliğini içeriğine göre ayarla (scrollable_frame)
        content_height = scrollable_frame.winfo_reqheight()
        canvas.config(height=content_height)


if __name__ == "__main__":
    root = tk.Tk()
    app = HammingGUI(root)
    root.mainloop()