# kalkulasi/nutrisi_tanah.py
"""
Modul Manajemen Nutrisi Edafik dan Formulasi Pemupukan Baku PPKS.
Mengimplementasikan:
1. Dinamika Neraca Hara NPK & Fiksasi Nitrogen Simbiotik (Substitusi Urea).
2. Kompensasi Pupuk Kalium (MOP / KCl) pada Tanaman Sela Rakus Kalium.
3. Formulasi Pembenah Tanah Dolomit Berfaktor Tekstur (pH < 4.5).
"""

from typing import Dict, Any

def calculate_npk_balance(
    crop_type: str,
    palm_age_years: float,
    land_area_ha: float
) -> Dict[str, Any]:
    """
    Menghitung dinamika neraca hara NPK berdasarkan baku mutu agronomi PPKS:
    - Legum: Fiksasi N2 60-70 kg N/ha -> Substitusi Urea = 65 / 0.46 = 141.3 kg Urea/ha/tahun.
    - Rimpang/Umbi: Kompensasi Kalium = 45 kg K2O/ha -> 75.0 kg MOP/KCl (60% K2O)/ha/tahun di lorong gawangan.
    """
    c_lower = (crop_type or "").lower()

    if any(k in c_lower for k in ["kedelai", "kacang", "soybean", "peanut", "legum", "legume", "mucuna"]):
        biological_n_fixation_kg_ha = 65.0
        urea_equiv_saved_kg_ha = round(65.0 / 0.46, 2)  # ~141.3 kg Urea/ha
        total_urea_saved_kg = round(urea_equiv_saved_kg_ha * land_area_ha, 2)
        k2o_demand_kg_ha = 0.0
        mop_fertilizer_demand_kg_ha = 0.0
        total_mop_demand_kg = 0.0
        advisory_id = "Fiksasi N simbiotik aktif (Rhizobium). Aplikasi pupuk Urea di piringan sawit dapat dihemat sebesar 141.3 kg/ha/tahun."
        advisory_en = "Active symbiotic N-fixation (Rhizobium). Palm circle Urea application rate can be safely reduced by 141.3 kg/ha/year."
        nutrient_profile = "N-Fixing Symbiont (Leguminosae)"
    elif any(k in c_lower for k in ["jahe", "ginger", "curcuma", "temulawak", "kunyit", "porang", "tuber", "ubi", "kapulaga", "cardamom"]):
        biological_n_fixation_kg_ha = 0.0
        urea_equiv_saved_kg_ha = 0.0
        total_urea_saved_kg = 0.0
        k2o_demand_kg_ha = 45.0
        mop_fertilizer_demand_kg_ha = round(45.0 / 0.60, 2)  # 75.0 kg MOP (60% K2O)/ha
        total_mop_demand_kg = round(mop_fertilizer_demand_kg_ha * land_area_ha, 2)
        advisory_id = "Tanaman sela rakus Kalium. Aplikasikan tambahan pupuk MOP/KCl sebesar 75 kg/ha (45 kg K2O) di lorong gawangan agar tidak bersaing dengan pelepah sawit."
        advisory_en = "Potassium-demanding intercrop. Supplement inter-row alleys with 75 kg/ha MOP/KCl (45 kg K2O) to prevent competition with palm fronds."
        nutrient_profile = "Heavy Potassium Consumer (Rhizome / Tuber)"
    else:
        biological_n_fixation_kg_ha = 15.0
        urea_equiv_saved_kg_ha = round(15.0 / 0.46, 2)
        total_urea_saved_kg = round(urea_equiv_saved_kg_ha * land_area_ha, 2)
        k2o_demand_kg_ha = 20.0
        mop_fertilizer_demand_kg_ha = round(20.0 / 0.60, 2)
        total_mop_demand_kg = round(mop_fertilizer_demand_kg_ha * land_area_ha, 2)
        advisory_id = "Kebutuhan hara NPK seimbang. Pertahankan pemupukan sawit standar dan aplikasikan mulsa biomassa di lorong gawangan."
        advisory_en = "Balanced NPK requirement. Maintain standard palm fertilization and apply biomass mulch in alley corridors."
        nutrient_profile = "Neutral / Moderate Feeder"

    return {
        "nutrient_profile": nutrient_profile,
        "biological_n_fixation_kg_ha": biological_n_fixation_kg_ha,
        "urea_equivalent_saved_kg_ha": urea_equiv_saved_kg_ha,
        "total_urea_saved_kg": total_urea_saved_kg,
        "k2o_demand_kg_ha": k2o_demand_kg_ha,
        "mop_fertilizer_demand_kg_ha": mop_fertilizer_demand_kg_ha,
        "total_mop_demand_kg": total_mop_demand_kg,
        "agronomic_advisory_id": advisory_id,
        "agronomic_advisory_en": advisory_en
    }

def calculate_soil_amendment_recommendation(
    soil_ph: float,
    soil_texture: str = "sandy_loam"
) -> Dict[str, Any]:
    """
    Menghitung dosis dolomit CaMg(CO3)2 per hektar berdasarkan toleransi baku pH PPKS (pH >= 4.5):
    Formula: Dosis (ton/ha) = (4.5 - pH) * 1.2 * F_tekstur
    Faktor koreksi: Lempung berpasir (1.0), Liat berat (1.15), Gambut (1.25).
    """
    text_norm = str(soil_texture or "sandy_loam").lower().strip()

    if soil_ph < 4.5:
        base_dose = (4.5 - soil_ph) * 1.2
        if any(k in text_norm for k in ["clay", "liat"]):
            texture_factor = 1.15
            texture_label = "Liat berat (faktor 1.15)"
        elif any(k in text_norm for k in ["peat", "gambut"]):
            texture_factor = 1.25
            texture_label = "Gambut / Histosol (faktor 1.25)"
        else:
            texture_factor = 1.0
            texture_label = "Lempung berpasir (faktor 1.0)"

        recommended_dolomite_ton_ha = round(base_dose * texture_factor, 2)
        is_required = True
        desc_id = (
            f"pH tanah masam ({soil_ph:.1f} < 4.5): Timbul toksisitas Al3+ dan retensi Fosfat. "
            f"Dosis dolomit rekomendasi: {recommended_dolomite_ton_ha:.2f} ton/ha = (4.5 - {soil_ph:.1f}) × 1.2 × {texture_factor} "
            f"({texture_label}). Tebar merata di lorong gawangan."
        )
        desc_en = (
            f"Acidic soil pH ({soil_ph:.1f} < 4.5): Aluminum (Al3+) toxicity and Phosphorus fixation risk. "
            f"Recommended dolomite rate: {recommended_dolomite_ton_ha:.2f} tons/ha ({texture_label})."
        )
    else:
        recommended_dolomite_ton_ha = 0.0
        is_required = False
        desc_id = f"pH tanah optimal ({soil_ph:.1f} >= 4.5): Reaksi tanah memenuhi baku mutu agronomis sawit."
        desc_en = f"Optimal soil pH ({soil_ph:.1f} >= 4.5): Soil reaction meets standard agronomic thresholds."

    return {
        "soil_ph": soil_ph,
        "target_ph": 4.5,
        "is_amendment_required": is_required,
        "recommended_dolomite_ton_ha": recommended_dolomite_ton_ha,
        "soil_texture_category": soil_texture,
        "advisory_description_id": desc_id,
        "advisory_description_en": desc_en
    }