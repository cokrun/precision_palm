# cloud_services/biophysics.py
"""
Deterministik In-Silico Biophysics & Agroforestry Calculation Engine for Precision Palm.
Menghitung model bio-fisika dan valuasi ekologis deterministik:
1. Hukum Beer-Lambert untuk transmisi Radiasi Fotosintesis Aktif (PAR) kanopi sawit.
2. Geometri kanopi spasial dan ketersediaan luas gawangan bersih (effective intercrop area).
3. Indeks Efisiensi Penggunaan Lahan (Land Equivalent Ratio / LER) menurut Mead & Willey.
4. Estimasi Pencegahan Alih Fungsi Lahan (Avoided Deforestation) dan Akumulasi Karbon (IPCC/Verra Tier 3).
5. Komparator Efisiensi Tapak Lahan (Percentage Land Saved / PLS).
6. Rekomendasi parameter tata ruang spasial dan agronomi optimal di gawangan kelapa sawit.
7. Valuasi bio-ekonomi gabungan (panen sela + kredit karbon).
8. Neraca hara NPK terpadu.
9. Evaluasi bioklimatologi dan kesesuaian tanah FAO/Djaenudin.
"""

import math
from typing import Dict, Any, Optional


def calculate_leaf_area_index(
    palm_age_years: float,
    lai_max: float = 5.5,
    growth_rate: float = 0.7,
    t0_inflection: float = 3.5
) -> float:
    if palm_age_years < 0:
        raise ValueError("Umur kelapa sawit tidak boleh bernilai negatif.")
    return lai_max / (1.0 + math.exp(-growth_rate * (palm_age_years - t0_inflection)))


def calculate_beer_lambert_transmission(
    lai: float,
    i0_par: float = 1800.0,
    k_extinction: float = 0.45
) -> Dict[str, float]:
    if lai < 0:
        raise ValueError("Nilai LAI tidak boleh bernilai negatif.")
    if i0_par < 0 or k_extinction < 0:
        raise ValueError("Nilai I0 PAR dan koefisien k tidak boleh negatif.")

    transmitted_fraction = math.exp(-k_extinction * lai)
    transmitted_par = i0_par * transmitted_fraction
    canopy_shading_percentage = (1.0 - transmitted_fraction) * 100.0

    return {
        "leaf_area_index": round(lai, 3),
        "canopy_shading_pct": round(canopy_shading_percentage, 2),
        "surface_par_umol_m2_s": round(transmitted_par, 2),
        "light_transmission_ratio": round(transmitted_fraction, 4)
    }


def calculate_canopy_transmission(
    palm_age_years: float, 
    i0_par: float = 1800.0, 
    k_extinction: float = 0.45
) -> Dict[str, float]:
    lai = calculate_leaf_area_index(palm_age_years=palm_age_years)
    rad_metrics = calculate_beer_lambert_transmission(
        lai=lai,
        i0_par=i0_par,
        k_extinction=k_extinction
    )
    return {
        "palm_age_years": palm_age_years,
        "leaf_area_index": rad_metrics["leaf_area_index"],
        "canopy_shading_pct": rad_metrics["canopy_shading_pct"],
        "surface_par_umol_m2_s": rad_metrics["surface_par_umol_m2_s"],
        "light_transmission_ratio": rad_metrics["light_transmission_ratio"]
    }


def calculate_canopy_geometry(
    palm_age_years: float,
    planting_density: int = 136
) -> Dict[str, float]:
    if palm_age_years < 0:
        raise ValueError("Umur kelapa sawit tidak boleh bernilai negatif.")
    if planting_density <= 0:
        raise ValueError("Kerapatan tanam kelapa sawit harus bernilai lebih besar dari 0.")

    frond_radius = 5.5 / (1.0 + math.exp(-0.6 * (palm_age_years - 3.5)))
    canopy_area_per_ha = planting_density * math.pi * (frond_radius ** 2)
    canopy_fraction = min(1.0, canopy_area_per_ha / 10000.0)
    canopy_cover_percentage = round(canopy_fraction * 100.0, 2)

    buffer_area_per_ha = planting_density * math.pi * (2.0 ** 2)
    buffer_fraction = buffer_area_per_ha / 10000.0
    unplanted_buffer_percentage = round(buffer_fraction * 100.0, 2)
    net_effective_percentage = round((1.0 - buffer_fraction) * 100.0, 2)

    return {
        "frond_radius_m": round(frond_radius, 2),
        "canopy_cover_pct": canopy_cover_percentage,
        "effective_intercrop_area_pct": net_effective_percentage,
        "unplanted_buffer_pct": unplanted_buffer_percentage
    }


def calculate_ler(
    yield_palm_intercrop: float,
    yield_palm_monoculture: float,
    yield_intercrop_actual: float,
    yield_intercrop_monoculture: float
) -> Dict[str, Any]:
    if yield_palm_monoculture <= 0 or yield_intercrop_monoculture <= 0:
        raise ValueError("Nilai panen monokultur referensi harus lebih besar dari 0.")
    if yield_palm_intercrop < 0 or yield_intercrop_actual < 0:
        raise ValueError("Nilai panen aktual tidak boleh bernilai negatif.")
        
    partial_ler_palm = yield_palm_intercrop / yield_palm_monoculture
    partial_ler_intercrop = yield_intercrop_actual / yield_intercrop_monoculture
    total_ler = partial_ler_palm + partial_ler_intercrop
    
    return {
        "partial_ler_palm": round(partial_ler_palm, 4),
        "partial_ler_intercrop": round(partial_ler_intercrop, 4),
        "total_ler": round(total_ler, 4),
        "is_yield_advantageous": total_ler > 1.0
    }


def calculate_avoided_deforestation(
    land_area_ha: float,
    total_ler: float,
    forest_carbon_stock_tco2e_per_ha: float = 450.0,
    annual_soil_c_gain_per_ha: float = 1.8
) -> Dict[str, Any]:
    if land_area_ha < 0:
        raise ValueError("Luas lahan kebun tidak boleh bernilai negatif.")

    if total_ler <= 1.0:
        return {
            "planted_land_area_ha": land_area_ha,
            "avoided_land_ha": 0.0,
            "avoided_emission_tco2e": 0.0,
            "annual_soil_c_gain_tco2e": 0.0,
            "total_climate_benefit_tco2e": 0.0,
            "status": "Monokultur lebih efisien atau tidak ada keunggulan lahan."
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
        "status": "Signifikan mencegah alih fungsi lahan tropis."
    }


def calculate_land_efficiency_comparator(
    land_area_ha: float,
    total_ler: float
) -> Dict[str, Any]:
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


def calculate_optimal_agroforestry_parameters(
    palm_age_years: float,
    crop_category: str = "general"
) -> Dict[str, Any]:
    if palm_age_years < 0:
        raise ValueError("Umur kelapa sawit tidak boleh bernilai negatif.")
        
    if palm_age_years <= 3.0:
        buffer_radius = 2.0
    elif palm_age_years <= 7.0:
        buffer_radius = 2.2
    else:
        buffer_radius = 2.5

    corridor_width = round(max(1.5, 9.0 - (2.0 * buffer_radius)), 2)
    max_deficit_pct = 4.5
    cat = (crop_category or "general").lower()
    
    if any(k in cat for k in ["ginger", "jahe", "curcuma", "temulawak", "kunyit", "rhizome"]):
        detected_category = "Rhizome & Medicinal Spices"
        inter_row = 0.50
        intra_row = 0.40
        population = 45000
    elif any(k in cat for k in ["legume", "soybean", "kedelai", "peanut", "kacang"]):
        detected_category = "Grain Legumes (N-Fixing)"
        inter_row = 0.40
        intra_row = 0.20
        population = 160000
    elif any(k in cat for k in ["cereal", "maize", "jagung", "sorghum", "sorgum"]):
        detected_category = "Cereals & Food Staples"
        inter_row = 0.75
        intra_row = 0.25
        population = 50000
    elif any(k in cat for k in ["porang", "tuber", "ubi", "sweet potato"]):
        detected_category = "Understory Tubers (Araceae / Convolvulaceae)"
        inter_row = 0.80
        intra_row = 0.50
        population = 22000
    elif any(k in cat for k in ["vanilla", "vanili"]):
        detected_category = "Climbing Shade Orchids"
        inter_row = 1.50
        intra_row = 1.00
        population = 2000
    elif any(k in cat for k in ["cardamom", "kapulaga"]):
        detected_category = "Extreme Shade Spices (Zingiberaceae)"
        inter_row = 1.20
        intra_row = 1.00
        population = 3200
    else:
        detected_category = "General Intercrop"
        inter_row = 0.60
        intra_row = 0.40
        population = 30000

    return {
        "recommended_buffer_radius_m": buffer_radius,
        "clear_intercrop_corridor_width_m": corridor_width,
        "optimal_inter_row_spacing_m": inter_row,
        "optimal_intra_row_spacing_m": intra_row,
        "max_allowable_palm_yield_deficit_pct": max_deficit_pct,
        "recommended_population_per_ha": population,
        "crop_category_detected": detected_category
    }


def calculate_economic_valuation(
    crop_type: str,
    intercrop_yield_ton_ha: float,
    land_area_ha: float,
    carbon_benefit_tco2e: float,
    carbon_price_usd: float = 12.0,
    usd_to_idr: float = 16000.0
) -> Dict[str, Any]:
    c_lower = (crop_type or "").lower()
    
    if any(k in c_lower for k in ["jahe", "ginger", "curcuma", "temulawak", "kunyit"]):
        price_per_kg = 25000.0
        commodity_label = "Jahe Merah / Rimpang Medis"
    elif any(k in c_lower for k in ["kapulaga", "cardamom", "amomum"]):
        price_per_kg = 85000.0
        commodity_label = "Kapulaga / Cardamom (Amomum compactum)"
    elif any(k in c_lower for k in ["kedelai", "soybean", "kacang", "peanut"]):
        price_per_kg = 12000.0
        commodity_label = "Kedelai / Legum Butir"
    elif any(k in c_lower for k in ["porang", "tuber", "ubi", "sweet potato"]):
        price_per_kg = 8000.0
        commodity_label = "Porang / Umbi Naungan"
    elif any(k in c_lower for k in ["serai", "citronella", "nilam", "patchouli"]):
        price_per_kg = 6000.0
        commodity_label = "Serai Wangi / Atsiri"
    elif any(k in c_lower for k in ["vanili", "vanilla"]):
        price_per_kg = 150000.0
        commodity_label = "Vanili Kering Super"
    else:
        price_per_kg = 10000.0
        commodity_label = "Komoditas Sela Umum"

    effective_corridor_ratio = 0.83
    effective_corridor_ha = round(land_area_ha * effective_corridor_ratio, 2)

    gross_crop_revenue_idr = round(intercrop_yield_ton_ha * 1000.0 * price_per_kg * effective_corridor_ha, 2)
    gross_crop_revenue_usd = round(gross_crop_revenue_idr / usd_to_idr, 2)

    carbon_revenue_usd = round(max(0.0, carbon_benefit_tco2e) * carbon_price_usd, 2)
    carbon_revenue_idr = round(carbon_revenue_usd * usd_to_idr, 2)

    total_economic_benefit_idr = round(gross_crop_revenue_idr + carbon_revenue_idr, 2)
    total_economic_benefit_usd = round(gross_crop_revenue_usd + carbon_revenue_usd, 2)
    revenue_per_ha_usd = round(gross_crop_revenue_usd / max(0.1, land_area_ha), 2)
    price_per_kg_usd = round(price_per_kg / usd_to_idr, 2)

    return {
        "commodity_detected": commodity_label,
        "price_per_kg_idr": price_per_kg,
        "price_per_kg_usd": price_per_kg_usd,
        "effective_corridor_area_ha": effective_corridor_ha,
        "gross_crop_revenue_idr": gross_crop_revenue_idr,
        "gross_crop_revenue_usd": gross_crop_revenue_usd,
        "carbon_price_usd_per_ton": carbon_price_usd,
        "carbon_revenue_usd": carbon_revenue_usd,
        "carbon_revenue_idr": carbon_revenue_idr,
        "total_economic_benefit_idr": total_economic_benefit_idr,
        "total_economic_benefit_usd": total_economic_benefit_usd,
        "revenue_per_ha_usd": revenue_per_ha_usd,
        "exchange_rate_usd_idr": usd_to_idr
    }


def calculate_npk_balance(
    crop_type: str,
    palm_age_years: float,
    land_area_ha: float
) -> Dict[str, Any]:
    c_lower = (crop_type or "").lower()

    if any(k in c_lower for k in ["kedelai", "kacang", "soybean", "peanut", "legum", "legume"]):
        biological_n_fixation_kg_ha = 65.0
        urea_equiv_saved_kg_ha = round(biological_n_fixation_kg_ha / 0.46, 2)
        total_urea_saved_kg = round(urea_equiv_saved_kg_ha * land_area_ha, 2)
        k2o_demand_kg_ha = 0.0
        total_k2o_demand_kg = 0.0
        advisory_id = "Fiksasi N simbiotik aktif (Rhizobium). Dosis pupuk Urea di piringan sawit dapat dikurangi secara aman hingga 140 kg/ha/tahun."
        advisory_en = "Active symbiotic N-fixation (Rhizobium). Palm circle Urea application rate can be safely reduced by up to 140 kg/ha/year."
        nutrient_profile = "N-Fixing Symbiont (Leguminosae)"
    elif any(k in c_lower for k in ["jahe", "ginger", "curcuma", "temulawak", "kunyit", "porang", "tuber", "ubi", "kapulaga", "cardamom"]):
        biological_n_fixation_kg_ha = 0.0
        urea_equiv_saved_kg_ha = 0.0
        total_urea_saved_kg = 0.0
        k2o_demand_kg_ha = 45.0
        total_k2o_demand_kg = round(k2o_demand_kg_ha * land_area_ha, 2)
        advisory_id = "Tanaman sela rakus Kalium. Tambahkan aplikasi pupuk MOP/KCl khusus pada gawangan (45 kg K2O/ha) agar tidak bersaing dengan pelepah sawit."
        advisory_en = "Potassium-demanding intercrop. Supplement inter-row alleys with dedicated MOP/KCl fertilizer (45 kg K2O/ha) to prevent nutrient competition with palm fronds."
        nutrient_profile = "Heavy Potassium Consumer (Rhizome / Tuber)"
    else:
        biological_n_fixation_kg_ha = 15.0
        urea_equiv_saved_kg_ha = round(15.0 / 0.46, 2)
        total_urea_saved_kg = round(urea_equiv_saved_kg_ha * land_area_ha, 2)
        k2o_demand_kg_ha = 20.0
        total_k2o_demand_kg = round(k2o_demand_kg_ha * land_area_ha, 2)
        advisory_id = "Kebutuhan hara NPK berimbang. Pertahankan pemupukan sawit standar dan aplikasikan mulsa biomassa di lorong gawangan."
        advisory_en = "Balanced NPK requirement. Maintain standard palm fertilization and apply organic biomass mulch in alley corridors."
        nutrient_profile = "Neutral / Moderate Feeder"

    return {
        "nutrient_profile": nutrient_profile,
        "biological_n_fixation_kg_ha": biological_n_fixation_kg_ha,
        "urea_equivalent_saved_kg_ha": urea_equiv_saved_kg_ha,
        "total_urea_saved_kg": total_urea_saved_kg,
        "k2o_demand_kg_ha": k2o_demand_kg_ha,
        "total_k2o_demand_kg": total_k2o_demand_kg,
        "agronomic_advisory": advisory_id,
        "agronomic_advisory_id": advisory_id,
        "agronomic_advisory_en": advisory_en
    }


def calculate_water_deficit_and_yield_impact(annual_rainfall_mm: float) -> Dict[str, Any]:
    if annual_rainfall_mm < 1500.0:
        water_deficit_mm = round(1500.0 - annual_rainfall_mm, 1)
        severity = "MODERATE" if water_deficit_mm < 300.0 else ("SEVERE" if water_deficit_mm < 600.0 else "EXTREME")
        tbs_reduction_pct = min(45.0, round((water_deficit_mm / 1500.0) * 100.0 * 0.85, 1))
        female_flower_abortion_pct = min(40.0, round((water_deficit_mm / 1500.0) * 100.0 * 0.70, 1))
        timeline_id = "12 - 24 bulan ke depan (Lag fase inisiasi primordia infloresensi ke pematangan tandan)"
        timeline_en = "12 - 24 months forward lag (Inflorescence primordia differentiation to bunch ripening)"
        desc_id = (
            f"Peringatan Defisit Air: Curah hujan ({annual_rainfall_mm:.1f} mm/tahun) berada di bawah batas kritis 1.500 mm "
            f"(defisit akumulatif {water_deficit_mm:.1f} mm). Memicu aborsi bunga betina (+{female_flower_abortion_pct}%) "
            f"dan diproyeksikan menurunkan produksi TBS sebesar {tbs_reduction_pct}% pada siklus 12–24 bulan ke depan."
        )
        desc_en = (
            f"Water Deficit Warning: Annual precipitation ({annual_rainfall_mm:.1f} mm/year) is below the critical 1,500 mm threshold "
            f"(accumulated deficit {water_deficit_mm:.1f} mm). Induces female inflorescence abortion (+{female_flower_abortion_pct}%) "
            f"and projects an estimated FFB yield reduction of {tbs_reduction_pct}% over the 12–24 months forward cycle."
        )
    else:
        water_deficit_mm = 0.0
        severity = "NONE"
        tbs_reduction_pct = 0.0
        female_flower_abortion_pct = 0.0
        timeline_id = "Normal (Ketersediaan air mencukupi, tidak ada proyeksi penurunan TBS)"
        timeline_en = "Normal (Adequate water availability, no FFB yield suppression projected)"
        desc_id = (
            f"Ketersediaan air optimal ({annual_rainfall_mm:.1f} mm/tahun >= 1.500 mm). "
            f"Diferensiasi seks primordia bunga betina dan pembentukan TBS berjalan normal."
        )
        desc_en = (
            f"Optimal water availability ({annual_rainfall_mm:.1f} mm/year >= 1,500 mm). "
            f"Inflorescence sex differentiation and FFB bunch formation proceed under favorable conditions."
        )

    return {
        "annual_rainfall_mm": annual_rainfall_mm,
        "water_deficit_mm": water_deficit_mm,
        "deficit_severity": severity,
        "tbs_yield_reduction_projected_pct": tbs_reduction_pct,
        "female_flower_abortion_projected_pct": female_flower_abortion_pct,
        "impact_timeline_months": "12-24",
        "impact_projection_timeline_id": timeline_id,
        "impact_projection_timeline_en": timeline_en,
        "advisory_description_id": desc_id,
        "advisory_description_en": desc_en
    }


def calculate_microclimate_buffering(
    intercrop_canopy_cover_pct: float = 65.0,
    palm_age_years: float = 6.0
) -> Dict[str, Any]:
    cov_ratio = max(0.0, min(1.0, intercrop_canopy_cover_pct / 100.0))
    soil_evap_reduction_pct = round(25.0 + (cov_ratio * 10.0), 1)
    soil_temp_reduction_c = round(2.0 + (cov_ratio * 2.0), 1)
    moisture_retention_gain_pct = round(15.0 + (cov_ratio * 15.0), 1)

    scientific_basis_id = (
        "Integrasi tutupan tajuk tanaman sela di lorong gawangan membentuk kanopi sekunder yang menaungi tanah, "
        f"mereduksi suhu permukaan tanah sebesar {soil_temp_reduction_c:.1f}°C dan memotong laju evaporasi air tanah "
        f"sebesar {soil_evap_reduction_pct:.1f}% dibanding lahan monokultur terbuka. Kondisi ini menjaga kadar air tanah "
        "tersedia (available water capacity) di zona perakaran serabut sawit selama periode kering."
    )
    scientific_basis_en = (
        "Secondary intercrop canopy cover inside alley corridors shades the plantation floor, "
        f"lowering topsoil surface temperature by {soil_temp_reduction_c:.1f}°C and curtailing soil moisture evaporation "
        f"by {soil_evap_reduction_pct:.1f}% compared to bare open monoculture soil. This microclimatic buffering preserves "
        "soil matric water potential in active palm feeder root zones during dry intervals."
    )

    return {
        "intercrop_canopy_cover_pct": intercrop_canopy_cover_pct,
        "soil_evaporation_reduction_pct": soil_evap_reduction_pct,
        "soil_temperature_reduction_c": soil_temp_reduction_c,
        "moisture_retention_gain_pct": moisture_retention_gain_pct,
        "buffering_status": "ACTIVE_BUFFERING",
        "scientific_basis_id": scientific_basis_id,
        "scientific_basis_en": scientific_basis_en
    }


def calculate_soil_amendment_recommendation(
    soil_ph: float,
    soil_texture: str = "sandy_loam"
) -> Dict[str, Any]:
    text_norm = str(soil_texture or "sandy_loam").lower().strip()
    
    if soil_ph < 4.5:
        base_dose = (4.5 - soil_ph) * 1.2
        if any(k in text_norm for k in ["clay", "liat", "lempung_berat"]):
            texture_factor = 1.15
            texture_note_id = "Tekstur liat: daya sangga KTK tinggi (+15% dolomit)"
            texture_note_en = "Heavy clay texture: high CEC buffering (+15% dolomite)"
        elif any(k in text_norm for k in ["peat", "gambut"]):
            texture_factor = 1.25
            texture_note_id = "Tanah gambut: kemasaman asam organik tinggi (+25% dolomit bertahap)"
            texture_note_en = "Peat soil: high organic acid content (+25% split dolomite)"
        else:
            texture_factor = 1.0
            texture_note_id = "Tekstur lempung berpasir standar"
            texture_note_en = "Standard sandy loam texture"

        recommended_dolomite_ton_ha = round(base_dose * texture_factor, 2)
        is_required = True
        desc_id = (
            f"pH tanah masam ({soil_ph:.1f} < 4.5): Terjadi risiko toksisitas Aluminium (Al3+) dan fiksasi Fosfat. "
            f"Dosis rekomendasi dolomit: {recommended_dolomite_ton_ha:.2f} ton/ha = (4.5 - {soil_ph:.1f}) × 1.2 "
            f"({texture_note_id}). Tebar merata di lorong gawangan dan batas luar piringan steril."
        )
        desc_en = (
            f"Acidic soil pH ({soil_ph:.1f} < 4.5): Risk of Aluminum (Al3+) toxicity and Phosphorus fixation. "
            f"Recommended dolomite dosage: {recommended_dolomite_ton_ha:.2f} tons/ha = (4.5 - {soil_ph:.1f}) × 1.2 "
            f"({texture_note_en}). Broadcast uniformly in alley corridors and outer ring of sterile circle."
        )
    else:
        recommended_dolomite_ton_ha = 0.0
        is_required = False
        desc_id = (
            f"pH tanah optimal ({soil_ph:.1f} >= 4.5): Reaksi tanah berada dalam jendela serapan hara ideal. "
            "Aplikasi dolomit korektif tidak diperlukan; pertahankan pemeliharaan rutin."
        )
        desc_en = (
            f"Optimal soil pH ({soil_ph:.1f} >= 4.5): Soil reaction is within the optimal bio-available nutrient window. "
            "Corrective dolomite liming is not required; maintain routine agronomic upkeep."
        )

    return {
        "soil_ph": soil_ph,
        "target_ph": 4.5,
        "is_amendment_required": is_required,
        "recommended_dolomite_ton_ha": recommended_dolomite_ton_ha,
        "soil_texture_category": soil_texture,
        "advisory_description_id": desc_id,
        "advisory_description_en": desc_en
    }


def evaluate_temperature_humidity_stress(
    mean_temperature_c: float,
    relative_humidity_pct: float
) -> Dict[str, Any]:
    temp_optimal = 24.0 <= mean_temperature_c <= 28.0
    rh_optimal = 70.0 <= relative_humidity_pct <= 90.0

    if temp_optimal and rh_optimal:
        is_stress = False
        stress_status = "OPTIMAL_VIGOUR"
        desc_id = (
            f"Kondisi bioklimat ideal (Suhu {mean_temperature_c:.1f}°C, RH {relative_humidity_pct:.1f}%). "
            "Konduktansi stomata maksimal, laju transpirasi seimbang, dan asimilasi fotosintesis kanopi berjalan optimal."
        )
        desc_en = (
            f"Optimal bioclimatic conditions (Temperature {mean_temperature_c:.1f}°C, RH {relative_humidity_pct:.1f}%). "
            "Maximal stomatal conductance, balanced transpiration, and peak photosynthetic assimilation."
        )
    else:
        is_stress = True
        stress_status = "STOMATA_PHYSIOLOGICAL_STRESS"
        desc_id = (
            f"Stres fisiologis stomata terdeteksi (Suhu {mean_temperature_c:.1f}°C, RH {relative_humidity_pct:.1f}%). "
            "Potensial memicu penutupan stomata dan pembatasan transpirasi."
        )
        desc_en = (
            f"Physiological stomatal stress detected (Temperature {mean_temperature_c:.1f}°C, RH {relative_humidity_pct:.1f}%). "
            "Potentially triggers stomatal closure and transpiration restriction."
        )

    return {
        "mean_temperature_c": mean_temperature_c,
        "relative_humidity_pct": relative_humidity_pct,
        "is_stomata_stress": is_stress,
        "stress_status": stress_status,
        "temperature_optimal": temp_optimal,
        "humidity_optimal": rh_optimal,
        "advisory_description_id": desc_id,
        "advisory_description_en": desc_en
    }


def calculate_bioclimatic_soil_suitability(
    annual_rainfall_mm: float = 2000.0,
    mean_temperature_c: float = 26.5,
    relative_humidity_pct: float = 80.0,
    sunshine_hours_day: float = 6.0,
    soil_ph: float = 5.5,
    soil_texture: str = "sandy_loam",
    drainage_condition: str = "good",
    npk_status: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    water_deficit_data = calculate_water_deficit_and_yield_impact(annual_rainfall_mm)
    microclimate_data = calculate_microclimate_buffering(intercrop_canopy_cover_pct=65.0)
    soil_amendment_data = calculate_soil_amendment_recommendation(soil_ph, soil_texture)
    stomata_stress_data = evaluate_temperature_humidity_stress(mean_temperature_c, relative_humidity_pct)

    if 1500.0 <= annual_rainfall_mm <= 2500.0:
        rf_score = 100.0
        rf_status = "OPTIMAL"
        rf_desc_id = "Curah hujan ideal (1.500–2.500 mm/tahun) terdistribusi merata."
        rf_desc_en = "Optimal annual rainfall (1,500–2,500 mm/year)."
    elif annual_rainfall_mm < 1500.0:
        rf_score = max(30.0, round(100.0 - (1500.0 - annual_rainfall_mm) * 0.08, 1))
        rf_status = "WATER_DEFICIT"
        rf_desc_id = water_deficit_data["advisory_description_id"]
        rf_desc_en = water_deficit_data["advisory_description_en"]
    else:
        rf_score = max(50.0, round(100.0 - (annual_rainfall_mm - 2500.0) * 0.04, 1))
        rf_status = "WATER_EXCESS"
        rf_desc_id = "Peringatan Curah Hujan Berlebih: Curah hujan >2.500 mm/tahun."
        rf_desc_en = "Excessive Rainfall Warning: Annual rainfall >2,500 mm/year."

    if 24.0 <= mean_temperature_c <= 28.0:
        temp_score = 100.0
        temp_status = "OPTIMAL"
        temp_desc_id = "Suhu udara optimal (24–28°C)."
        temp_desc_en = "Optimal mean temperature (24–28°C)."
    elif (20.0 <= mean_temperature_c < 24.0) or (28.0 < mean_temperature_c <= 32.0):
        temp_score = 75.0
        temp_status = "MODERATE"
        temp_desc_id = "Suhu udara dalam batas toleransi kelapa sawit."
        temp_desc_en = "Temperature within tolerable growth thresholds."
    else:
        temp_score = 45.0
        temp_status = "PHYSIOLOGICAL_STRESS"
        temp_desc_id = "Peringatan Stres Fisiologis: Suhu ekstrem (>32°C atau <20°C)."
        temp_desc_en = "Physiological Stress Warning: Extreme temperatures."

    if 70.0 <= relative_humidity_pct <= 90.0:
        rh_score = 100.0
        rh_status = "OPTIMAL"
        rh_desc_id = "Kelembapan udara ideal (70–90%)."
        rh_desc_en = "Optimal relative humidity (70–90%)."
    elif relative_humidity_pct < 70.0:
        rh_score = 70.0
        rh_status = "LOW_HUMIDITY"
        rh_desc_id = "Kelembapan udara rendah (<70%)."
        rh_desc_en = "Low humidity (<70%)."
    else:
        rh_score = 75.0
        rh_status = "HIGH_HUMIDITY_SATURATED"
        rh_desc_id = "Kelembapan udara sangat tinggi (>90%)."
        rh_desc_en = "Saturated humidity (>90%)."

    if sunshine_hours_day >= 5.0:
        sun_score = 100.0
        sun_status = "OPTIMAL"
        sun_desc_id = "Penyinaran matahari memadai (>=5 jam/hari)."
        sun_desc_en = "Sufficient sunshine duration (>=5 hrs/day)."
    else:
        sun_score = max(40.0, round(sunshine_hours_day * 15.0, 1))
        sun_status = "DEFICIT_RADIATION"
        sun_desc_id = "Penyinaran matahari kurang (<5 jam/hari)."
        sun_desc_en = "Insolation deficit (<5 hrs/day)."

    if 4.5 <= soil_ph <= 6.5:
        ph_score = 100.0
        ph_status = "OPTIMAL"
        ph_desc_id = "Reaksi tanah ideal (pH 4.5–6.5)."
        ph_desc_en = "Optimal soil reaction (pH 4.5–6.5)."
    elif soil_ph < 4.0:
        ph_score = 45.0
        ph_status = "EXTREMELY_ACIDIC"
        ph_desc_id = soil_amendment_data["advisory_description_id"]
        ph_desc_en = soil_amendment_data["advisory_description_en"]
    elif 4.0 <= soil_ph < 4.5:
        ph_score = 70.0
        ph_status = "MODERATELY_ACIDIC"
        ph_desc_id = soil_amendment_data["advisory_description_id"]
        ph_desc_en = soil_amendment_data["advisory_description_en"]
    else:
        ph_score = 70.0
        ph_status = "ALKALINE_CHALK"
        ph_desc_id = "Reaksi tanah agak alkalis/netral (pH > 6.5)."
        ph_desc_en = "Mildly alkaline/neutral soil (pH > 6.5)."

    text_norm = str(soil_texture or "sandy_loam").lower().strip()
    if any(k in text_norm for k in ["sandy_loam", "lempung_berpasir", "loam"]):
        tex_score = 100.0
        tex_status = "OPTIMAL"
        tex_label = "Sandy Loam (Lempung Berpasir)"
        tex_desc_id = "Tekstur Lempung Berpasir: Aerasi perakaran sangat baik."
        tex_desc_en = "Sandy Loam Texture: Excellent root zone aeration."
    elif any(k in text_norm for k in ["clay", "liat", "lempung"]):
        tex_score = 75.0
        tex_status = "SLOW_DRAINAGE_COMPACT"
        tex_label = "Clay (Liat / Lempung Berat)"
        tex_desc_id = "Tekstur Liat: Kapasitas simpan hara tinggi, drainase lambat."
        tex_desc_en = "Heavy Clay Texture: High CEC nutrient retention."
    elif any(k in text_norm for k in ["peat", "gambut"]):
        tex_score = 65.0
        tex_status = "PEAT_MANAGEMENT_REQUIRED"
        tex_label = "Peat (Tanah Gambut)"
        tex_desc_id = "Tanah Gambut: Daya dukung mekanis rendah."
        tex_desc_en = "Peat Soil: Low mechanical bearing capacity."
    else:
        tex_score = 80.0
        tex_status = "GENERAL_SOIL"
        tex_label = "General Soil / Tanah Umum"
        tex_desc_id = "Tekstur tanah sedang: Aerasi wajar."
        tex_desc_en = "Medium soil texture: Aeration normal."

    drain_norm = str(drainage_condition or "good").lower().strip()
    drain_status = "FREE_DRAINAGE_GOOD"
    drain_score = 100.0
    drain_desc_id = "Kondisi drainase lancar."
    drain_desc_en = "Free-draining condition."

    npk_dict = npk_status or {"nitrogen": "adequate", "phosphorus": "adequate", "potassium": "adequate"}
    npk_eval = {
        "nitrogen_status": npk_dict.get("nitrogen", "adequate"),
        "phosphorus_status": npk_dict.get("phosphorus", "adequate"),
        "potassium_status": npk_dict.get("potassium", "adequate"),
        "summary_id": "Status hara NPK tanah terpantau stabil.",
        "summary_en": "Soil NPK status monitored stable."
    }

    composite_score = round(
        (rf_score * 0.30) +
        (temp_score * 0.20) +
        (rh_score * 0.15) +
        (sun_score * 0.10) +
        (ph_score * 0.15) +
        (tex_score * 0.10),
        1
    )

    if composite_score >= 85.0:
        suitability_class = "S1"
        suitability_label_id = "S1 - Sangat Sesuai (Highly Suitable)"
        suitability_label_en = "S1 - Highly Suitable"
    elif composite_score >= 70.0:
        suitability_class = "S2"
        suitability_label_id = "S2 - Cukup Sesuai (Moderately Suitable)"
        suitability_label_en = "S2 - Moderately Suitable"
    elif composite_score >= 55.0:
        suitability_class = "S3"
        suitability_label_id = "S3 - Sesuai Marginal (Marginally Suitable)"
        suitability_label_en = "S3 - Marginally Suitable"
    else:
        suitability_class = "N"
        suitability_label_id = "N - Tidak Sesuai (Not Suitable / Pembatas Berat)"
        suitability_label_en = "N - Not Suitable (Severe Limitations)"

    return {
        "suitability_score_pct": composite_score,
        "suitability_class": suitability_class,
        "suitability_label_id": suitability_label_id,
        "suitability_label_en": suitability_label_en,
        "parameters": {
            "annual_rainfall_mm": annual_rainfall_mm,
            "rainfall_status": rf_status,
            "rainfall_score": rf_score,
            "rainfall_desc_id": rf_desc_id,
            "rainfall_desc_en": rf_desc_en,
            "mean_temperature_c": mean_temperature_c,
            "temperature_status": temp_status,
            "temperature_score": temp_score,
            "temperature_desc_id": temp_desc_id,
            "temperature_desc_en": temp_desc_en,
            "relative_humidity_pct": relative_humidity_pct,
            "humidity_status": rh_status,
            "humidity_score": rh_score,
            "humidity_desc_id": rh_desc_id,
            "humidity_desc_en": rh_desc_en,
            "sunshine_hours_day": sunshine_hours_day,
            "sunshine_status": sun_status,
            "sunshine_score": sun_score,
            "sunshine_desc_id": sun_desc_id,
            "sunshine_desc_en": sun_desc_en,
            "soil_ph": soil_ph,
            "soil_ph_status": ph_status,
            "soil_ph_score": ph_score,
            "soil_ph_desc_id": ph_desc_id,
            "soil_ph_desc_en": ph_desc_en,
            "soil_texture": tex_label,
            "soil_texture_status": tex_status,
            "soil_texture_score": tex_score,
            "soil_texture_desc_id": tex_desc_id,
            "soil_texture_desc_en": tex_desc_en,
            "drainage_condition": drain_norm,
            "drainage_status": drain_status,
            "drainage_score": drain_score,
            "drainage_desc_id": drain_desc_id,
            "drainage_desc_en": drain_desc_en
        },
        "water_deficit_analysis": water_deficit_data,
        "microclimate_buffering": microclimate_data,
        "soil_amendment_recommendation": soil_amendment_data,
        "stomata_physiological_stress": stomata_stress_data,
        "npk_availability": npk_eval
    }


def simulate_agroforestry_system(
    palm_age_years: float,
    land_area_ha: float,
    yield_palm_intercrop: float,
    yield_palm_monoculture: float,
    yield_intercrop_actual: float,
    yield_intercrop_monoculture: float,
    crop_name: str = "Tanaman Sela",
    planting_density: int = 136,
    i0_par: float = 1800.0,
    k_extinction: float = 0.45,
    forest_carbon_stock: float = 450.0,
    soil_c_rate: float = 1.8,
    annual_rainfall_mm: float = 2000.0,
    mean_temperature_c: float = 26.5,
    relative_humidity_pct: float = 80.0,
    sunshine_hours_day: float = 6.0,
    soil_ph: float = 5.5,
    soil_texture: str = "sandy_loam"
) -> Dict[str, Any]:
    canopy_res = calculate_canopy_transmission(palm_age_years, i0_par, k_extinction)
    geom_res = calculate_canopy_geometry(palm_age_years, planting_density)
    ler_res = calculate_ler(yield_palm_intercrop, yield_palm_monoculture, yield_intercrop_actual, yield_intercrop_monoculture)
    avoid_res = calculate_avoided_deforestation(land_area_ha, ler_res["total_ler"], forest_carbon_stock, soil_c_rate)
    comp_res = calculate_land_efficiency_comparator(land_area_ha, ler_res["total_ler"])
    params_res = calculate_optimal_agroforestry_parameters(palm_age_years, crop_name)
    econ_res = calculate_economic_valuation(crop_name, yield_intercrop_actual, land_area_ha, avoid_res["total_climate_benefit_tco2e"])
    npk_res = calculate_npk_balance(crop_name, palm_age_years, land_area_ha)
    bio_res = calculate_bioclimatic_soil_suitability(
        annual_rainfall_mm=annual_rainfall_mm,
        mean_temperature_c=mean_temperature_c,
        relative_humidity_pct=relative_humidity_pct,
        sunshine_hours_day=sunshine_hours_day,
        soil_ph=soil_ph,
        soil_texture=soil_texture
    )

    return {
        "canopy_transmission": canopy_res,
        "canopy_geometry": geom_res,
        "land_equivalent_ratio": ler_res,
        "avoided_deforestation": avoid_res,
        "efficiency_comparator": comp_res,
        "optimal_parameters": params_res,
        "economic_valuation": econ_res,
        "npk_balance": npk_res,
        "bioclimatic_suitability": bio_res
    }
