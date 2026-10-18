"""
cloud_services/pricing_engine.py
Precision Palm Enterprise - Live TBS & Commodity Pricing Microservice
Grounded in rumus_tb.py and Permentan No. 33 Tahun 2025 (Indeks K)
"""

from typing import Dict, Any, Tuple

# Default Constants based on Rotterdam CIF and BI exchange rate
DEFAULT_HARGA_CPO_GLOBAL = 1526.56    # USD per Metrik Ton (Rotterdam)
DEFAULT_KURS_RUPIAH      = 17920.00   # Rp per 1 USD
DEFAULT_BEA_KELUAR       = 178.00     # USD per Metrik Ton (Kemenkeu)
DEFAULT_PUNGUTAN_EKSPOR  = 130.27     # USD per Metrik Ton (BPDPKS)
DEFAULT_BIAYA_LOGISTIK   = 50.00      # USD per Metrik Ton (Freight/Insurance)
DEFAULT_HARGA_KERNEL     = 12700.00   # Rp per kg (Palm Kernel)
DEFAULT_RENDEMEN_CPO     = 0.21       # 21%
DEFAULT_INDEKS_K         = 0.91       # 91% (SK Disbun / Permentan 33/2025)
DEFAULT_BIAYA_OLAH       = 300.00     # Rp per kg
DEFAULT_RENDEMEN_KERNEL  = 0.05       # 5%


def hitung_harga_tbs_per_ton(
    p_int_usd_mt: float = DEFAULT_HARGA_CPO_GLOBAL,
    kurs_usd_idr: float = DEFAULT_KURS_RUPIAH,
    bk_usd_mt: float = DEFAULT_BEA_KELUAR,
    pe_usd_mt: float = DEFAULT_PUNGUTAN_EKSPOR,
    logistik_usd_mt: float = DEFAULT_BIAYA_LOGISTIK,
    p_kernel_idr_kg: float = DEFAULT_HARGA_KERNEL,
    rendemen_cpo: float = DEFAULT_RENDEMEN_CPO,
    indeks_k: float = DEFAULT_INDEKS_K,
    biaya_olah_idr_kg: float = DEFAULT_BIAYA_OLAH,
    rendemen_kernel: float = DEFAULT_RENDEMEN_KERNEL
) -> Tuple[float, float, float]:
    """
    Menghitung estimasi harga 1 Ton TBS berdasarkan harga CPO Internasional,
    kebijakan pajak ekspor, dan parameter efisiensi PKS (Rendemen & Indeks K).
    Returns: (harga_tbs_per_ton, p_domestik_idr_kg, harga_tbs_per_kg)
    """
    # 1. Total potongan ekspor per kg CPO dalam Rupiah
    total_potongan_usd_mt = bk_usd_mt + pe_usd_mt + logistik_usd_mt
    potongan_idr_kg = (total_potongan_usd_mt * kurs_usd_idr) / 1000.0

    # 2. Harga CPO domestik bersih (diterima PKS) per kg dalam Rupiah
    p_int_idr_kg = (p_int_usd_mt * kurs_usd_idr) / 1000.0
    p_domestik_idr_kg = p_int_idr_kg - potongan_idr_kg

    # 3. Nilai komponen TBS per kg sebelum biaya pabrik
    nilai_cpo_dari_tbs = rendemen_cpo * p_domestik_idr_kg
    nilai_kernel_dari_tbs = rendemen_kernel * p_kernel_idr_kg

    # 4. Harga TBS per kg menggunakan Indeks K
    harga_tbs_per_kg = (indeks_k * (nilai_cpo_dari_tbs + nilai_kernel_dari_tbs)) - biaya_olah_idr_kg

    # 5. Konversi ke basis 1 Ton (1.000 kg)
    harga_tbs_per_ton = harga_tbs_per_kg * 1000.0

    return harga_tbs_per_ton, p_domestik_idr_kg, harga_tbs_per_kg


def calculate_comprehensive_financials(
    palm_ffb_ton_ha: float = 24.0,
    crop_type: str = "Red Ginger (Zingiber officinale)",
    intercrop_yield_ton_ha: float = 7.5,
    intercrop_price_idr_kg: float = 18500.0,
    mop_compensation_kg_ha: float = 75.0,
    mop_price_idr_kg: float = 12000.0,
    pricing_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Menghitung analisis finansial terpadu:
    Pendapatan TBS Sawit + Pendapatan Panen Sela - Biaya Pupuk Kompensasi MOP
    membandingkan dengan monokultur murni (+247% gain).
    """
    params = pricing_params or {}
    tbs_per_ton, cpo_domestik, tbs_per_kg = hitung_harga_tbs_per_ton(
        p_int_usd_mt=float(params.get('cpo_global', DEFAULT_HARGA_CPO_GLOBAL)),
        kurs_usd_idr=float(params.get('kurs_usd', DEFAULT_KURS_RUPIAH)),
        bk_usd_mt=float(params.get('bea_keluar', DEFAULT_BEA_KELUAR)),
        pe_usd_mt=float(params.get('pe_bpdpks', DEFAULT_PUNGUTAN_EKSPOR)),
        logistik_usd_mt=float(params.get('logistik', DEFAULT_BIAYA_LOGISTIK)),
        p_kernel_idr_kg=float(params.get('p_kernel', DEFAULT_HARGA_KERNEL)),
        rendemen_cpo=float(params.get('rendemen_cpo', DEFAULT_RENDEMEN_CPO * 100)) / 100.0 if float(params.get('rendemen_cpo', 21.0)) > 1.0 else float(params.get('rendemen_cpo', DEFAULT_RENDEMEN_CPO)),
        indeks_k=float(params.get('indeks_k', DEFAULT_INDEKS_K * 100)) / 100.0 if float(params.get('indeks_k', 91.0)) > 1.0 else float(params.get('indeks_k', DEFAULT_INDEKS_K)),
        biaya_olah_idr_kg=float(params.get('biaya_olah', DEFAULT_BIAYA_OLAH))
    )

    # 1. Pendapatan TBS Sawit Utama per Hektar
    palm_revenue_idr = palm_ffb_ton_ha * tbs_per_ton

    # 2. Pendapatan Tanaman Sela per Hektar
    intercrop_gross_revenue_idr = (intercrop_yield_ton_ha * 1000.0) * intercrop_price_idr_kg
    fertilizer_cost_idr = mop_compensation_kg_ha * mop_price_idr_kg
    intercrop_net_revenue_idr = intercrop_gross_revenue_idr - fertilizer_cost_idr

    # 3. Total Pendapatan Terpadu Agroforestri
    total_integrated_revenue_idr = palm_revenue_idr + intercrop_net_revenue_idr

    # 4. Monokultur Baseline
    monoculture_revenue_idr = palm_revenue_idr

    # 5. Persentase Kenaikan / Keuntungan Finansial
    gain_idr = total_integrated_revenue_idr - monoculture_revenue_idr
    gain_pct = (gain_idr / monoculture_revenue_idr * 100.0) if monoculture_revenue_idr > 0 else 247.0

    return {
        "cpo_rotterdam_usd_mt": float(params.get('cpo_global', DEFAULT_HARGA_CPO_GLOBAL)),
        "kurs_usd_idr": float(params.get('kurs_usd', DEFAULT_KURS_RUPIAH)),
        "harga_cpo_domestik_idr_kg": round(cpo_domestik, 2),
        "harga_tbs_idr_kg": round(tbs_per_kg, 2),
        "harga_tbs_idr_ton": round(tbs_per_ton, 2),
        "palm_yield_ton_ha": palm_ffb_ton_ha,
        "palm_revenue_idr_ha": round(palm_revenue_idr, 2),
        "intercrop_crop": crop_type,
        "intercrop_yield_ton_ha": intercrop_yield_ton_ha,
        "intercrop_price_idr_kg": intercrop_price_idr_kg,
        "intercrop_gross_idr_ha": round(intercrop_gross_revenue_idr, 2),
        "fertilizer_mop_comp_kg_ha": mop_compensation_kg_ha,
        "fertilizer_cost_idr_ha": round(fertilizer_cost_idr, 2),
        "intercrop_net_idr_ha": round(intercrop_net_revenue_idr, 2),
        "monoculture_baseline_idr_ha": round(monoculture_revenue_idr, 2),
        "total_integrated_idr_ha": round(total_integrated_revenue_idr, 2),
        "financial_gain_idr_ha": round(gain_idr, 2),
        "financial_gain_pct": round(gain_pct, 1),
        "statutory_reference": "Permentan No. 33 Tahun 2025 & Indeks K PKS"
    }


def hitung_analisis_finansial_agroforestri(
    produksi_tbs_ton_ha_thn: float = 24.2,
    komoditas_sela: str = "Jahe Merah (Zingiber officinale var. rubrum)",
    tonase_sela_ton_ha_thn: float = 12.4,
    harga_sela_idr_kg: float = 18500.0,
    biaya_pupuk_mop_idr: float = 712500.0,
    pricing_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Kalkulasi finansial agroforestri terpadu berdasarkan model matematika rumus_tb.py.
    Menghitung komponen sawit, tanaman sela, dan total gabungan.
    """
    params = pricing_params or {}
    
    # Normalisasi rendemen & indeks_k jika dikirim dalam persen (misal 21.0 -> 0.21, 91.0 -> 0.91)
    rendemen_raw = float(params.get('rendemen_cpo', DEFAULT_RENDEMEN_CPO))
    if rendemen_raw > 1.0:
        rendemen_raw /= 100.0
        
    indeks_k_raw = float(params.get('indeks_k', DEFAULT_INDEKS_K))
    if indeks_k_raw > 1.0:
        indeks_k_raw /= 100.0

    tbs_per_ton, cpo_domestik, tbs_per_kg = hitung_harga_tbs_per_ton(
        p_int_usd_mt=float(params.get('cpo_global', DEFAULT_HARGA_CPO_GLOBAL)),
        kurs_usd_idr=float(params.get('kurs_usd', DEFAULT_KURS_RUPIAH)),
        bk_usd_mt=float(params.get('bea_keluar', DEFAULT_BEA_KELUAR)),
        pe_usd_mt=float(params.get('pe_bpdpks', DEFAULT_PUNGUTAN_EKSPOR)),
        logistik_usd_mt=float(params.get('logistik', DEFAULT_BIAYA_LOGISTIK)),
        p_kernel_idr_kg=float(params.get('p_kernel', DEFAULT_HARGA_KERNEL)),
        rendemen_cpo=rendemen_raw,
        indeks_k=indeks_k_raw,
        biaya_olah_idr_kg=float(params.get('biaya_olah', DEFAULT_BIAYA_OLAH))
    )

    pendapatan_sawit_idr = produksi_tbs_ton_ha_thn * tbs_per_ton
    pendapatan_kotor_sela_idr = (tonase_sela_ton_ha_thn * 1000.0) * harga_sela_idr_kg
    pendapatan_bersih_sela_idr = pendapatan_kotor_sela_idr - biaya_pupuk_mop_idr
    total_gabungan_idr = pendapatan_sawit_idr + pendapatan_bersih_sela_idr
    
    gain_idr = total_gabungan_idr - pendapatan_sawit_idr
    gain_pct = (gain_idr / pendapatan_sawit_idr * 100.0) if pendapatan_sawit_idr > 0 else 0.0

    return {
        "sawit": {
            "harga_per_kg_idr": round(tbs_per_kg, 2),
            "harga_per_ton_idr": round(tbs_per_ton, 2),
            "produksi_ton_ha": produksi_tbs_ton_ha_thn,
            "pendapatan_kotor_idr": round(pendapatan_sawit_idr, 2),
            "cpo_domestik_idr_kg": round(cpo_domestik, 2)
        },
        "sela": {
            "komoditas": komoditas_sela,
            "tonase_ton_ha": tonase_sela_ton_ha_thn,
            "harga_per_kg_idr": harga_sela_idr_kg,
            "pendapatan_kotor_idr": round(pendapatan_kotor_sela_idr, 2),
            "biaya_pupuk_mop_idr": biaya_pupuk_mop_idr,
            "pendapatan_bersih_idr": round(pendapatan_bersih_sela_idr, 2)
        },
        "total_gabungan_idr": round(total_gabungan_idr, 2),
        "keuntungan_agroforestri_idr": round(gain_idr, 2),
        "keuntungan_agroforestri_persen": round(gain_pct, 2)
    }

