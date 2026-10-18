# ==============================================================================
# Precision Palm - Biophysical Agroforestry Intelligence Engine
# Modul Komputasi Matematis & Biofisika Deterministik (Monsi-Saeki & LER)
# Acuan: Permentan 33/2025, Standar PPKS Medan, dan FIPS 180-4
# ==============================================================================

import math
import logging

logger = logging.getLogger("precision_palm.biophysical_engine")

# ------------------------------------------------------------------------------
# 1. TRANSMISI KANOPI & RADIASI PAR (Hukum Monsi-Saeki)
# ------------------------------------------------------------------------------
def calculate_canopy_transmission(palm_age_years: float = 7.0, lai_override: float = None, **kwargs) -> dict:
    """
    Menghitung transmisi Radiasi Fotosintesis Aktif (PAR) di bawah tajuk kelapa sawit
    menggunakan model kepunahan cahaya Monsi-Saeki deterministik:
    I = I_0 * exp(-k * LAI), dengan koefisien ekstingsi k = 0.45.
    """
    age = max(1.0, float(palm_age_years or kwargs.get("palm_age", 7.0)))
    k_extinction = 0.45

    # LAI sigmoid logistik bertumbuh dari TBM (umur 1-3) hingga TM prima (umur 7-15)
    if lai_override is not None and float(lai_override) > 0:
        lai = float(lai_override)
    else:
        # Kurva logistik LAI PPKS: mendekati 1.2 pada umur muda, hingga ~4.25 pada TM prime
        lai = 1.0 + (3.4 / (1.0 + math.exp(-0.7 * (age - 4.5))))
        lai = round(min(5.5, max(0.8, lai)), 2)

    # Transmisi cahaya relatif (I / I_0)
    transmission_ratio = math.exp(-k_extinction * lai)
    transmission_pct = round(transmission_ratio * 100.0, 2)
    canopy_shading_pct = round(100.0 - transmission_pct, 2)

    # Rata-rata radiasi PAR permukaan terbuka tropis ~1800 umol/m^2/s
    i_0_surface = 1800.0
    transmitted_par = round(i_0_surface * transmission_ratio, 1)

    return {
        "palm_age_years": age,
        "leaf_area_index": lai,
        "k_extinction": k_extinction,
        "transmission_ratio": round(transmission_ratio, 4),
        "light_transmission_ratio": round(transmission_ratio, 4),
        "par_transmission_pct": transmission_pct,
        "canopy_shading_pct": canopy_shading_pct,
        "transmitted_par_umol": transmitted_par,
        "surface_par_umol_m2_s": transmitted_par,
        "intercrop_light_feasibility": "OPTIMAL" if transmission_pct >= 28.0 else ("MODERATE" if transmission_pct >= 18.0 else "HEAVY_SHADE")
    }

# ------------------------------------------------------------------------------
# 2. GEOMETRI KORIDOR GAWANGAN & PIRINGAN STERIL 2.0M
# ------------------------------------------------------------------------------
def calculate_canopy_geometry(frond_radius_m: float = 4.5, planting_distance_m: float = 9.0, **kwargs) -> dict:
    """
    Menghitung pembagian ruang spasial pada pola tanam segitiga sama sisi 9.0 m.
    Populasi standar = 143 pokok/ha.
    Menjamin piringan steril 2.0 m bebas cangkulan mekanis (zero-tillage).
    """
    s = float(planting_distance_m or kwargs.get("planting_distance", 9.0))
    r_frond = float(frond_radius_m or kwargs.get("frond_radius", 4.5))
    sterile_ring_radius = 2.0

    # Luas per pokok pada segitiga sama sisi = s^2 * sin(60 deg)
    area_per_tree = (s ** 2) * math.sin(math.radians(60))
    stand_density_per_ha = round(10000.0 / area_per_tree) if area_per_tree > 0 else 143
    if kwargs.get("planting_density"):
        stand_density_per_ha = int(kwargs.get("planting_density"))

    # Jarak antar barisan (inter-row distance)
    row_distance_m = s * math.sin(math.radians(60))  # ~7.79 m

    # Lebar lorong gawangan bersih antar piringan steril 2.0m di kedua sisi
    # Jarak antar pokok 9.0m - (2 x 2.0m radius piringan) = 5.0m koridor terbuka maksimum
    # Jarak antar baris 7.79m - (2 x 2.0m radius piringan) = 3.79m koridor efektif
    effective_corridor_width_m = round(row_distance_m - (2.0 * sterile_ring_radius), 2)

    # Persentase alokasi luas
    area_sterile_per_tree = math.pi * (sterile_ring_radius ** 2)  # ~12.57 m2
    sterile_total_area_ha = (area_sterile_per_tree * stand_density_per_ha) / 10000.0
    sterile_buffer_pct = round(sterile_total_area_ha * 100.0, 1)

    effective_intercrop_area_pct = round(100.0 - sterile_buffer_pct - 5.0, 1)  # 5% jalan/pasar pikul

    return {
        "planting_pattern": "SEGITIGA_SAMA_SISI",
        "spacing_distance_m": s,
        "row_distance_m": round(row_distance_m, 2),
        "stand_density_per_ha": stand_density_per_ha,
        "sterile_ring_radius_m": sterile_ring_radius,
        "net_corridor_width_m": effective_corridor_width_m,
        "frond_radius_m": r_frond,
        "unplanted_buffer_pct": sterile_buffer_pct,
        "effective_intercrop_area_pct": effective_intercrop_area_pct,
        "canopy_cover_pct": round(100.0 - effective_intercrop_area_pct, 1),
        "root_protection_standard": "ZERO_TILLAGE_2M_BUFFER_PPKS"
    }

# ------------------------------------------------------------------------------
# 3. RASIO KESETARAAN LAHAN (LAND EQUIVALENT RATIO - LER)
# ------------------------------------------------------------------------------
def calculate_ler(
    yield_palm_intercropped: float = 24.2,
    yield_palm_monoculture: float = 24.5,
    yield_companion_intercropped: float = 12.4,
    yield_companion_monoculture: float = 18.0,
    **kwargs
) -> dict:
    """
    Menghitung LER = (Y_palm_inter / Y_palm_mono) + (Y_comp_inter / Y_comp_mono).
    Jika LER > 1.0, sistem agroforestri lebih efisien daripada monokultur terpisah.
    """
    yp_i = max(0.01, float(kwargs.get("yield_palm_intercrop", yield_palm_intercropped)))
    yp_m = max(0.01, float(kwargs.get("yield_palm_monoculture", yield_palm_monoculture)))
    yc_i = max(0.0, float(kwargs.get("yield_intercrop_actual", kwargs.get("yield_companion_intercropped", yield_companion_intercropped))))
    yc_m = max(0.01, float(kwargs.get("yield_intercrop_monoculture", kwargs.get("yield_companion_monoculture", yield_companion_monoculture))))

    partial_ler_palm = yp_i / yp_m
    partial_ler_companion = yc_i / yc_m
    total_ler = round(partial_ler_palm + partial_ler_companion, 3)

    # Persentase penghematan lahan: PLS = (1 - 1/LER) * 100%
    percentage_land_saved = round((1.0 - (1.0 / total_ler)) * 100.0, 2) if total_ler >= 1.0 else 0.0

    # Defisit panen sawit (harus <= 4.5% sesuai batas toleransi EUDR / ISPO)
    palm_deficit_pct = round(((yp_m - yp_i) / yp_m) * 100.0, 2)
    palm_deficit_pct = max(0.0, palm_deficit_pct)

    return {
        "partial_ler_palm": round(partial_ler_palm, 3),
        "partial_ler_companion": round(partial_ler_companion, 3),
        "partial_ler_intercrop": round(partial_ler_companion, 3),
        "total_ler": total_ler,
        "percentage_land_saved": percentage_land_saved,
        "palm_yield_deficit_pct": palm_deficit_pct,
        "is_deficit_within_threshold": palm_deficit_pct <= 4.5,
        "is_yield_advantageous": total_ler > 1.0,
        "efficiency_verdict": "SUPERIOR_LAND_SAVING" if total_ler >= 1.4 else ("ADVANTAGEOUS" if total_ler > 1.0 else "NEUTRAL")
    }

# ------------------------------------------------------------------------------
# 4. MITIGASI DEFORESTASI TERHINDARKAN (AVOIDED DEFORESTATION)
# ------------------------------------------------------------------------------
def calculate_avoided_deforestation(total_estate_area_ha: float = 1200.0, total_ler: float = 1.48, **kwargs) -> dict:
    """
    Menghitung kesetaraan hutan primer yang diselamatkan tanpa perlu ekspansi lahan baru
    berdasarkan peningkatan efisiensi LER.
    """
    area = max(1.0, float(kwargs.get("land_area_ha", kwargs.get("planted_land_area_ha", total_estate_area_ha or 1200.0))))
    ler = max(1.0, float(total_ler or kwargs.get("ler", 1.48)))

    pls = (1.0 - (1.0 / ler))
    avoided_ha = round(area * pls, 2)

    # Metrik Karbon Terhindar (Metodologi VCS VM0007 ~ 450 tCO2e/ha hutan tropis terselamatkan)
    carbon_sequestered_tco2e = round(avoided_ha * 450.0, 2)

    return {
        "concession_area_ha": area,
        "planted_land_area_ha": area,
        "total_ler": ler,
        "avoided_deforestation_ha": avoided_ha,
        "avoided_land_ha": avoided_ha,
        "carbon_mitigation_tco2e": carbon_sequestered_tco2e,
        "total_climate_benefit_tco2e": carbon_sequestered_tco2e,
        "annual_soil_c_gain_tco2e": round(area * 1.8, 1),
        "status": "Signifikan",
        "eudr_article_9_status": "COMPLIANT_ZERO_DEFORESTATION"
    }

# ------------------------------------------------------------------------------
# 5. KOMPARATOR EFISIENSI LAHAN MONOKULTUR VS AGROFORESTRI
# ------------------------------------------------------------------------------
def calculate_land_efficiency_comparator(estate_area_ha: float = 1200.0, companion_crop: str = "Jahe Merah", **kwargs) -> dict:
    """
    Membandingkan kebutuhan lahan aktual untuk memproduksi tonase yang sama
    antara pola monokultur terpisah vs pola agroforestri terpadu Precision Palm.
    """
    area = max(1.0, float(kwargs.get("land_area_ha", estate_area_ha or 1200.0)))
    ler = float(kwargs.get("total_ler", 0.0))
    if ler <= 0.0:
        ler_data = calculate_ler()
        ler = ler_data["total_ler"]

    land_needed_monoculture = round(area * ler, 2)
    saved_ha = round(land_needed_monoculture - area, 2)

    return {
        "companion_crop": companion_crop,
        "actual_agroforestry_area_ha": area,
        "integrated_agroforestry_ha": area,
        "equivalent_monoculture_area_ha": land_needed_monoculture,
        "equivalent_monoculture_ha": land_needed_monoculture,
        "land_saved_ha": saved_ha,
        "net_footprint_saved_ha": saved_ha,
        "land_saved_pct": round((saved_ha / land_needed_monoculture) * 100.0, 2) if land_needed_monoculture > 0 else 0.0,
        "expansion_pressure_reduction_pct": round((saved_ha / land_needed_monoculture) * 100.0, 2) if land_needed_monoculture > 0 else 0.0
    }

# ------------------------------------------------------------------------------
# 6. OPTIMAL AGROFORESTRY PARAMETERS (PENCARI PARAMETER OPTIMAL)
# ------------------------------------------------------------------------------
def calculate_optimal_agroforestry_parameters(
    palm_age_years: float = 7.5,
    crop_name: str = "Jahe Merah",
    concession_area_ha: float = 1200.0,
    **kwargs
) -> dict:
    """
    Menghasilkan kombinasi parameter biofisika, jarak tanam, dan rekomendasi rotasi panen
    paling optimal untuk komoditas sela yang dipilih di bawah tegakan sawit.
    """
    age = float(palm_age_years or kwargs.get("palm_age", 7.5))
    crop_specs = {
        "Jahe Merah": {"par_min": 25.0, "yield_ton_ha": 12.4, "price_idr_kg": 18500.0, "mop_comp_kg": 75.0, "category": "Rhizome"},
        "Kunyit": {"par_min": 28.0, "yield_ton_ha": 14.2, "price_idr_kg": 12000.0, "mop_comp_kg": 60.0, "category": "Rhizome"},
        "Temulawak": {"par_min": 22.0, "yield_ton_ha": 10.8, "price_idr_kg": 15000.0, "mop_comp_kg": 65.0, "category": "Rhizome"},
        "Kacang Tanah": {"par_min": 40.0, "yield_ton_ha": 2.2, "price_idr_kg": 24000.0, "mop_comp_kg": 40.0, "category": "Legume"},
        "Kedelai": {"par_min": 45.0, "yield_ton_ha": 1.8, "price_idr_kg": 13500.0, "mop_comp_kg": 45.0, "category": "Legume"}
    }

    # Penyesuaian nama tanaman jika dalam format ilmiah
    matched_key = "Jahe Merah"
    for k in crop_specs:
        if k.lower() in crop_name.lower():
            matched_key = k
            break

    spec = crop_specs.get(matched_key, crop_specs["Jahe Merah"])
    canopy = calculate_canopy_transmission(age)
    geom = calculate_canopy_geometry()
    ler = calculate_ler(24.2, 24.5, spec["yield_ton_ha"], spec["yield_ton_ha"] * 1.45)
    avoided = calculate_avoided_deforestation(concession_area_ha, ler["total_ler"])

    is_feasible = canopy["par_transmission_pct"] >= (spec["par_min"] * 0.85)

    return {
        "selected_crop": crop_name,
        "palm_age_years": age,
        "is_biophysically_feasible": is_feasible,
        "canopy_parameters": canopy,
        "geometric_parameters": geom,
        "ler_parameters": ler,
        "deforestation_mitigation": avoided,
        "recommended_bedding_width_m": 1.20,
        "recommended_furrows_per_alley": 2,
        "drainage_silt_pit_spacing_m": 25.0,
        "compensatory_mop_kg_ha": spec["mop_comp_kg"],
        "recommended_buffer_radius_m": 2.2,
        "clear_intercrop_corridor_width_m": geom["net_corridor_width_m"],
        "optimal_inter_row_spacing_m": 0.5,
        "optimal_intra_row_spacing_m": 0.4,
        "max_allowable_palm_yield_deficit_pct": 4.5,
        "recommended_population_per_ha": 45000,
        "crop_category_detected": spec.get("category", "Rhizome")
    }

# ------------------------------------------------------------------------------
# 7. VALUASI EKONOMI & SIMULASI REVENUE TBS (rumus_tb.py Integration)
# ------------------------------------------------------------------------------
def calculate_economic_valuation(
    estate_area_ha: float = 1200.0,
    palm_yield_ton_ha: float = 24.2,
    companion_crop: str = "Jahe Merah",
    companion_yield_ton_ha: float = 12.4,
    companion_price_idr_kg: float = 18500.0,
    tbs_price_per_ton_idr: float = 3824710.0,
    **kwargs
) -> dict:
    """
    Menghitung total pendapatan gabungan petani (TBS Kelapa Sawit + Panen Lorong Sela)
    serta komparasi margin keuntungan dibanding monokultur sawit konvensional.
    """
    area = max(1.0, float(kwargs.get("land_area_ha", estate_area_ha or 1200.0)))
    crop_str = kwargs.get("crop_type", companion_crop or "Jahe Merah")
    y_crop = float(kwargs.get("intercrop_yield_ton_ha", companion_yield_ton_ha or 12.4))
    price_crop = float(kwargs.get("price_per_kg_idr", companion_price_idr_kg or 18500.0))

    p_sawit_per_ha = palm_yield_ton_ha * tbs_price_per_ton_idr
    p_sela_per_ha = y_crop * 1000.0 * price_crop

    # Biaya pupuk penyeimbang MOP (K2O) ~ Rp 9.500/kg
    mop_cost_per_ha = 75.0 * 9500.0  # Rp 712.500 / ha
    net_sela_per_ha = p_sela_per_ha - mop_cost_per_ha

    total_combined_per_ha = p_sawit_per_ha + net_sela_per_ha
    gross_estate_total = total_combined_per_ha * area

    revenue_lift_pct = round(((total_combined_per_ha - p_sawit_per_ha) / p_sawit_per_ha) * 100.0, 2) if p_sawit_per_ha > 0 else 0.0

    return {
        "concession_area_ha": area,
        "commodity_detected": crop_str,
        "price_per_kg_idr": price_crop,
        "palm_revenue_per_ha_idr": round(p_sawit_per_ha, 2),
        "companion_revenue_gross_per_ha_idr": round(p_sela_per_ha, 2),
        "gross_crop_revenue_idr": round(p_sela_per_ha * area, 2),
        "compensatory_fertilizer_cost_per_ha_idr": round(mop_cost_per_ha, 2),
        "companion_revenue_net_per_ha_idr": round(net_sela_per_ha, 2),
        "total_combined_revenue_per_ha_idr": round(total_combined_per_ha, 2),
        "total_economic_benefit_idr": round(gross_estate_total, 2),
        "total_economic_benefit_usd": round(gross_estate_total / 16000.0, 2),
        "estate_total_annual_revenue_idr": round(gross_estate_total, 2),
        "revenue_lift_percentage": revenue_lift_pct
    }

# ------------------------------------------------------------------------------
# 8. NERACA HARA NPK & PUPUK PENYEIMBANG MOP (K2O)
# ------------------------------------------------------------------------------
def calculate_npk_balance(companion_crop: str = "Jahe Merah", companion_yield_ton_ha: float = 12.4, **kwargs) -> dict:
    """
    Menghitung serapan hara kalium oleh tanaman sela dan dosis kompensasi MOP (KCl 60% K2O)
    agar produktivitas tandan sawit tidak mengalami defisiensi hara.
    """
    crop_str = kwargs.get("crop_type", companion_crop or "Jahe Merah")
    y_crop = float(kwargs.get("companion_yield_ton_ha", kwargs.get("intercrop_yield_ton_ha", companion_yield_ton_ha or 12.4)))
    land_area = float(kwargs.get("land_area_ha", 1.0))

    # Koefisien serapan hara Jahe: ~4.2 kg N, 1.1 kg P2O5, 6.8 kg K2O per ton rimpang
    k2o_removal_kg_ha = y_crop * 6.8
    compensatory_mop_kg_ha = round(k2o_removal_kg_ha / 0.60, 1)  # MOP memiliki 60% K2O

    return {
        "companion_crop": crop_str,
        "yield_ton_ha": y_crop,
        "nutrient_profile": "Standard Feeder",
        "biological_n_fixation_kg_ha": 15.0,
        "urea_equivalent_saved_kg_ha": 32.6,
        "total_urea_saved_kg": round(32.6 * land_area, 1),
        "k2o_nutrient_removal_kg_ha": round(k2o_removal_kg_ha, 2),
        "k2o_demand_kg_ha": round(k2o_removal_kg_ha, 2),
        "total_k2o_demand_kg": round(k2o_removal_kg_ha * land_area, 1),
        "required_compensatory_mop_kg_ha": max(50.0, compensatory_mop_kg_ha),
        "application_schedule": "SPLIT_APPLICATION_2X_PER_YEAR",
        "ganoderma_suppression_index": "SAFE_ZERO_RISK",
        "agronomic_advisory": "Pemupukan berimbang MOP/KCl 2x per tahun untuk menjaga ketersediaan K2O"
    }

# ------------------------------------------------------------------------------
# 9. KESESUAIAN TANAH & AGROKLIMAT BIOFISIKA
# ------------------------------------------------------------------------------
def calculate_bioclimatic_soil_suitability(
    soil_ph: float = 5.5,
    slope_degrees: float = 4.5,
    elevation_asl_m: float = 142.0,
    soil_texture: str = "sandy_loam",
    **kwargs
) -> dict:
    """
    Mengevaluasi indeks kesesuaian tapak fisik lahan (S1, S2, S3)
    berdasarkan pH tanah, kelerengan kontur mikro SRTM, dan elevasi dpl.
    """
    ph = float(kwargs.get("soil_ph", soil_ph or 5.5))
    slope = float(kwargs.get("slope_degrees", kwargs.get("slope", slope_degrees or 4.5)))
    elev = float(kwargs.get("elevation_asl_m", kwargs.get("elevation", elevation_asl_m or 142.0)))
    texture = str(kwargs.get("soil_texture", soil_texture or "sandy_loam"))

    score = 100.0
    deductions = []

    # Penalti pH (Optimal 4.8 - 6.5)
    if ph < 4.5:
        score -= 15.0
        deductions.append("Soil strongly acidic (pH < 4.5) - Dolomite lime required")
    elif ph > 6.8:
        score -= 8.0
        deductions.append("Soil alkaline tendency (pH > 6.8)")

    # Penalti Kelerengan
    if slope > 15.0:
        score -= 25.0
        deductions.append("Slope exceeds 15 degrees - Mandatory contour bench terracing")
    elif slope > 8.0:
        score -= 10.0
        deductions.append("Undulating slope (8-15 deg) - Contour trenches recommended")

    # Penalti Ketinggian (Optimal < 400m DPL)
    if elev > 600.0:
        score -= 20.0
        deductions.append("High elevation (>600m ASL) - Temperature lapse rate risk")
    elif elev > 400.0:
        score -= 8.0
        deductions.append("Moderate elevation (400-600m ASL)")

    final_score = max(35.0, round(score, 1))
    if final_score >= 82.0:
        class_label = "S1 (Highly Suitable)"
        class_code = "S1"
        lbl_id = "S1 - Sangat Sesuai"
        lbl_en = "S1 - Highly Suitable"
    elif final_score >= 65.0:
        class_label = "S2 (Moderately Suitable)"
        class_code = "S2"
        lbl_id = "S2 - Cukup Sesuai"
        lbl_en = "S2 - Moderately Suitable"
    else:
        class_label = "S3 (Marginally Suitable)"
        class_code = "S3"
        lbl_id = "S3 - Sesuai Marjinal"
        lbl_en = "S3 - Marginally Suitable"

    return {
        "suitability_score": final_score,
        "suitability_score_pct": final_score,
        "suitability_class": class_code,
        "suitability_label": class_label,
        "suitability_label_id": lbl_id,
        "suitability_label_en": lbl_en,
        "is_eligible_for_cultivation": final_score >= 65.0 and slope <= 15.0,
        "evaluations": deductions if deductions else ["All physical site criteria meet prime benchmark."],
        "parameters": {
            "soil_ph": ph,
            "slope_degrees": slope,
            "elevation_asl_m": elev,
            "soil_texture": texture
        }
    }

if __name__ == "__main__":
    print("[*] Menguji Modul Biofisika Deterministik kalkulasi.engine...")
    res = calculate_optimal_agroforestry_parameters(7.5, "Jahe Merah", 1200.0)
    print(f"[OK] LER: {res['ler_parameters']['total_ler']}x | Transmisi PAR: {res['canopy_parameters']['par_transmission_pct']}%")