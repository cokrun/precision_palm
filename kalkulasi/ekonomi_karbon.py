# kalkulasi/ekonomi_karbon.py
"""
Modul Valuasi Ekonomi, Karbon Terhindar (Avoided Deforestation), dan Efisiensi Lahan.
Mengimplementasikan:
1. Land Equivalent Ratio (LER) menurut Mead & Willey (1980) & Verifikasi Defisit TBS <= 4.5%.
2. Pencegahan Alih Fungsi Hutan Primer (Avoided Deforestation / Verra VM0007 / IPCC Tier 3).
3. Percentage Land Saved (PLS) Komparator Tapak Lahan Fisik.
4. Estimasi Valuasi Bio-Ekonomi Bruto & Kredit Karbon (IDR & USD).
"""

from typing import Dict, Any

def calculate_ler(
    yield_palm_intercrop: float,
    yield_palm_monoculture: float,
    yield_intercrop_actual: float,
    yield_intercrop_monoculture: float
) -> Dict[str, Any]:
    """
    Menghitung LER sistem tumpang sari dan memverifikasi batas toleransi penurunan hasil sawit <= 4.5%.
    """
    if yield_palm_monoculture <= 0 or yield_intercrop_monoculture <= 0:
        raise ValueError("Nilai panen monokultur referensi harus lebih besar dari 0.")
    if yield_palm_intercrop < 0 or yield_intercrop_actual < 0:
        raise ValueError("Nilai panen aktual tidak boleh negatif.")

    partial_ler_palm = yield_palm_intercrop / yield_palm_monoculture
    partial_ler_intercrop = yield_intercrop_actual / yield_intercrop_monoculture
    total_ler = partial_ler_palm + partial_ler_intercrop

    palm_deficit_pct = max(0.0, round(((yield_palm_monoculture - yield_palm_intercrop) / yield_palm_monoculture) * 100.0, 2))
    is_deficit_within_limit = palm_deficit_pct <= 4.5

    return {
        "partial_ler_palm": round(partial_ler_palm, 4),
        "partial_ler_intercrop": round(partial_ler_intercrop, 4),
        "total_ler": round(total_ler, 4),
        "is_yield_advantageous": total_ler > 1.0,
        "palm_yield_deficit_pct": palm_deficit_pct,
        "is_deficit_tolerable": is_deficit_within_limit
    }

def calculate_avoided_deforestation(
    land_area_ha: float,
    total_ler: float,
    forest_carbon_stock_tco2e_per_ha: float = 450.0,
    annual_soil_c_gain_per_ha: float = 1.8
) -> Dict[str, Any]:
    """
    Menghitung pencegahan alih fungsi hutan tropis (Avoided Deforestation) merujuk pada metodologi Verra VM0007.
    """
    if land_area_ha < 0:
        raise ValueError("Luas lahan kebun tidak boleh bernilai negatif.")

    if total_ler <= 1.0:
        return {
            "planted_land_area_ha": land_area_ha,
            "avoided_land_ha": 0.0,
            "avoided_emission_tco2e": 0.0,
            "annual_soil_c_gain_tco2e": 0.0,
            "total_climate_benefit_tco2e": 0.0,
            "status": "SCENARIO_PROJECTION",
            "methodology_note": "Scenario only; no verified carbon stock, soil-carbon measurement, or project baseline was supplied."
        }

    avoided_land_ha = land_area_ha * (total_ler - 1.0)
    avoided_emission_tco2e = avoided_land_ha * forest_carbon_stock_tco2e_per_ha
    annual_soil_c_gain = land_area_ha * annual_soil_c_gain_per_ha
    total_benefit = avoided_emission_tco2e + annual_soil_c_gain

    return {
        "planted_land_area_ha": land_area_ha,
        "avoided_land_ha": round(avoided_land_ha, 2),
        "avoided_emission_tco2e": round(avoided_emission_tco2e, 2),
        "annual_soil_c_gain_tco2e": round(annual_soil_c_gain, 2),
        "total_climate_benefit_tco2e": round(total_benefit, 2),
        "status": "SCENARIO_PROJECTION",
        "methodology_note": (
            "Scenario only: applies illustrative factors of 450 tCO2e/ha for avoided land "
            "and 1.8 tCO2e/ha/year for soil-carbon gain. Not evidence of avoided deforestation "
            "or verified carbon credits."
        )
    }

def calculate_land_efficiency_comparator(
    land_area_ha: float,
    total_ler: float
) -> Dict[str, Any]:
    """Menghitung Percentage Land Saved (PLS) dan perbandingan tapak lahan fisik."""
    if land_area_ha < 0:
        raise ValueError("Luas lahan tidak boleh bernilai negatif.")

    if total_ler <= 1.0:
        return {
            "land_saved_pct": 0.0,
            "equivalent_monoculture_ha": round(land_area_ha, 2),
            "integrated_agroforestry_ha": round(land_area_ha, 2),
            "net_footprint_saved_ha": 0.0
        }

    pls = (1.0 - (1.0 / total_ler)) * 100.0
    equiv_mono = land_area_ha * total_ler
    net_saved = equiv_mono - land_area_ha

    return {
        "land_saved_pct": round(pls, 2),
        "equivalent_monoculture_ha": round(equiv_mono, 2),
        "integrated_agroforestry_ha": round(land_area_ha, 2),
        "net_footprint_saved_ha": round(net_saved, 2)
    }

def calculate_economic_valuation(
    crop_type: str,
    intercrop_yield_ton_ha: float,
    land_area_ha: float,
    carbon_benefit_tco2e: float,
    carbon_price_usd: float = 12.0,
    usd_to_idr: float = 16000.0
) -> Dict[str, Any]:
    """Melakukan estimasi valuasi bio-ekonomi panen komoditas sela dan kredit karbon."""
    c_lower = (crop_type or "").lower()

    if any(k in c_lower for k in ["jahe", "ginger"]):
        price_per_kg = 25000.0
    elif any(k in c_lower for k in ["kapulaga", "cardamom"]):
        price_per_kg = 85000.0
    elif any(k in c_lower for k in ["kedelai", "soybean"]):
        price_per_kg = 12000.0
    elif any(k in c_lower for k in ["porang"]):
        price_per_kg = 8000.0
    elif any(k in c_lower for k in ["vanili", "vanilla"]):
        price_per_kg = 150000.0
    else:
        price_per_kg = 15000.0

    effective_corridor_ratio = 0.83
    effective_corridor_ha = round(land_area_ha * effective_corridor_ratio, 2)

    gross_crop_revenue_idr = round(intercrop_yield_ton_ha * 1000.0 * price_per_kg * effective_corridor_ha, 2)
    gross_crop_revenue_usd = round(gross_crop_revenue_idr / usd_to_idr, 2)

    carbon_revenue_usd = round(max(0.0, carbon_benefit_tco2e) * carbon_price_usd, 2)
    carbon_revenue_idr = round(carbon_revenue_usd * usd_to_idr, 2)

    total_benefit_idr = round(gross_crop_revenue_idr + carbon_revenue_idr, 2)
    total_benefit_usd = round(gross_crop_revenue_usd + carbon_revenue_usd, 2)

    return {
        "price_per_kg_idr": price_per_kg,
        "effective_corridor_area_ha": effective_corridor_ha,
        "gross_crop_revenue_idr": gross_crop_revenue_idr,
        "gross_crop_revenue_usd": gross_crop_revenue_usd,
        "carbon_revenue_usd": carbon_revenue_usd,
        "carbon_revenue_idr": carbon_revenue_idr,
        "total_economic_benefit_idr": total_benefit_idr,
        "total_economic_benefit_usd": total_benefit_usd
    }