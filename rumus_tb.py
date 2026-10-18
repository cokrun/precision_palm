def hitung_harga_tbs_per_ton(
    p_int_usd_mt, 
    kurs_usd_idr, 
    bk_usd_mt, 
    pe_usd_mt, 
    logistik_usd_mt, 
    p_kernel_idr_kg, 
    rendemen_cpo, 
    indeks_k, 
    biaya_olah_idr_kg=300, 
    rendemen_kernel=0.05
):
    """
    Menghitung estimasi harga 1 Ton TBS berdasarkan harga CPO Internasional,
    kebijakan pajak ekspor, dan parameter efisiensi PKS (Rendemen & Indeks K).
    """
    # 1. Menghitung total potongan ekspor per kg CPO dalam Rupiah
    total_potongan_usd_mt = bk_usd_mt + pe_usd_mt + logistik_usd_mt
    potongan_idr_kg = (total_potongan_usd_mt * kurs_usd_idr) / 1000

    # 2. Menghitung harga CPO domestik bersih (diterima PKS) per kg dalam Rupiah
    p_int_idr_kg = (p_int_usd_mt * kurs_usd_idr) / 1000
    p_domestik_idr_kg = p_int_idr_kg - potongan_idr_kg

    # 3. Menghitung nilai komponen TBS per kg sebelum biaya pabrik
    nilai_cpo_dari_tbs = rendemen_cpo * p_domestik_idr_kg
    nilai_kernel_dari_tbs = rendemen_kernel * p_kernel_idr_kg

    # 4. Menghitung harga TBS per kg menggunakan Indeks K
    harga_tbs_per_kg = (indeks_k * (nilai_cpo_dari_tbs + nilai_kernel_dari_tbs)) - biaya_olah_idr_kg

    # 5. Konversi ke basis 1 Ton (1.000 kg)
    harga_tbs_per_ton = harga_tbs_per_kg * 1000

    return harga_tbs_per_ton, p_domestik_idr_kg, harga_tbs_per_kg


# =====================================================================
# SIMULASI PENGGUNAAN MODEL (Data Realitas Pasar Terbaru)
# =====================================================================
if __name__ == "__main__":
    # --- Input Variabel Pasar & Kebijakan Ekspor ---
    HARGA_CPO_GLOBAL = 1526.56   # USD per Metrik Ton (Rotterdam)
    KURS_RUPIAH      = 17920.00  # Rp per 1 USD
    BEA_KELUAR       = 178.00    # USD per Metrik Ton
    PUNGUTAN_EKSPOR  = 130.27    # USD per Metrik Ton (BPDPKS)
    BIAYA_LOGISTIK   = 50.00     # USD per Metrik Ton (Kapal/Asuransi)
    HARGA_KERNEL     = 12700.00  # Rp per Kilogram
    
    # --- Input Variabel Spesifik PKS Daerah Anda ---
    RENDEMEN_CPO_PKS = 0.21      # 21% (Tulis dalam desimal)
    INDEKS_K_PKS     = 0.91      # 91% (Tulis dalam desimal)

    # Menjalankan fungsi model
    tbs_per_ton, cpo_lokal, tbs_per_kg = hitung_harga_tbs_per_ton(
        p_int_usd_mt=HARGA_CPO_GLOBAL,
        kurs_usd_idr=KURS_RUPIAH,
        bk_usd_mt=BEA_KELUAR,
        pe_usd_mt=PUNGUTAN_EKSPOR,
        logistik_usd_mt=BIAYA_LOGISTIK,
        p_kernel_idr_kg=HARGA_KERNEL,
        rendemen_cpo=RENDEMEN_CPO_PKS,
        indeks_k=INDEKS_K_PKS
    )

    # Menampilkan hasil kalkulasi ke terminal
    print("=" * 55)
    print("      HASIL SIMULASI MODEL MATEMATIKA TBS & CPO      ")
    print("=" * 55)
    print(f"Harga Bersih CPO Domestik PKS : Rp {cpo_lokal:,.2f} / kg")
    print(f"Estimasi Harga TBS Petani     : Rp {tbs_per_kg:,.2f} / kg")
    print("-" * 55)
    print(f"HARGA ESTIMASI EKSAT PER TON TBS: Rp {tbs_per_ton:,.2f}")
    print("=" * 55)
