"""
Database Komprehensif Karakteristik Agronomi, Morfologi, dan Bio-Ekonomi
Tanaman Sela Agroforestri Kelapa Sawit (15 Komoditas Tropis Terstandarisasi).
Merujuk pada data Balittro, Balitkabi, PPKS, Balitbangtan, dan ICRAF.
"""

from typing import Dict, Any, List, Optional

CROPS_DATABASE: Dict[str, Dict[str, Any]] = {
"red_ginger": {
"key": "red_ginger",
"scientific_name": "Zingiber officinale var. rubrum",
"common_name_id": "Jahe Merah",
"common_name_en": "Red Ginger",
"category_id": "Rimpang Medis Bernilai Tinggi",
"category_en": "Medicinal Rhizome",
"palm_age_suitable_min": 4.0,
"palm_age_suitable_max": 9.0,
"shade_tolerance_pct": 30.0,
"optimal_par_umol": 800.0,
"optimal_soil_ph_min": 5.2,
"optimal_soil_ph_max": 6.8,
"preferred_soil_texture": "Lempung berpasir gembur kaya bahan organik",
"growing_period_months": 10,
"population_per_ha_effective": 45000,
"fresh_yield_ton_ha_mono": 15.0,
"fresh_yield_ton_ha_intercrop": 7.5,
"farmgate_price_idr_kg": 25000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 45.0,
"mop_supplement_kg_ha": 75.0,
"profile": "Konsumen Kalium Tinggi (Rimpang)"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 1.2,
"notes": "Tidak mengganggu perakaran sawit selama piringan 2.0m steril terjaga. Mulsa pelepah sawit menekan layu bakteri."
},
"labor_mandays_per_ha": 120
},
"curcuma": {
"key": "curcuma",
"scientific_name": "Curcuma zanthorrhiza",
"common_name_id": "Temulawak",
"common_name_en": "Javanese Turmeric",
"category_id": "Rimpang Adaptif Tahan Naungan",
"category_en": "Hardy Medicinal Rhizome",
"palm_age_suitable_min": 4.0,
"palm_age_suitable_max": 9.0,
"shade_tolerance_pct": 35.0,
"optimal_par_umol": 750.0,
"optimal_soil_ph_min": 5.0,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Lempung berpasir porous",
"growing_period_months": 9,
"population_per_ha_effective": 32000,
"fresh_yield_ton_ha_mono": 18.0,
"fresh_yield_ton_ha_intercrop": 9.2,
"farmgate_price_idr_kg": 18000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 40.0,
"mop_supplement_kg_ha": 66.7,
"profile": "Konsumen Kalium Sedang"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 1.1,
"notes": "Kadar kurkuminoid stabil pada naungan moderat. Sistem perakaran kompak di bedengan lorong gawangan."
},
"labor_mandays_per_ha": 95
},
"turmeric": {
"key": "turmeric",
"scientific_name": "Curcuma longa",
"common_name_id": "Kunyit",
"common_name_en": "Turmeric",
"category_id": "Rimpang Rempah & Industri",
"category_en": "Commercial Spice Rhizome",
"palm_age_suitable_min": 4.0,
"palm_age_suitable_max": 9.0,
"shade_tolerance_pct": 30.0,
"optimal_par_umol": 800.0,
"optimal_soil_ph_min": 5.2,
"optimal_soil_ph_max": 6.8,
"preferred_soil_texture": "Gembur subur berdrainase lancar",
"growing_period_months": 9,
"population_per_ha_effective": 40000,
"fresh_yield_ton_ha_mono": 14.0,
"fresh_yield_ton_ha_intercrop": 7.0,
"farmgate_price_idr_kg": 15000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 40.0,
"mop_supplement_kg_ha": 66.7,
"profile": "Konsumen Kalium Moderat"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 1.0,
"notes": "Sinergis dengan dekomposisi bahan organik pelepah cincang sawit."
},
"labor_mandays_per_ha": 90
},
"kencur": {
"key": "kencur",
"scientific_name": "Kaempferia galanga",
"common_name_id": "Kencur",
"common_name_en": "Aromatic Ginger",
"category_id": "Rimpang Aromatik Rendah",
"category_en": "Aromatic Rhizome",
"palm_age_suitable_min": 4.0,
"palm_age_suitable_max": 8.0,
"shade_tolerance_pct": 30.0,
"optimal_par_umol": 820.0,
"optimal_soil_ph_min": 5.5,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Lempung liat berpasir remah",
"growing_period_months": 8,
"population_per_ha_effective": 50000,
"fresh_yield_ton_ha_mono": 10.0,
"fresh_yield_ton_ha_intercrop": 5.5,
"farmgate_price_idr_kg": 30000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 35.0,
"mop_supplement_kg_ha": 58.3,
"profile": "Konsumen Fosfor & Kalium"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 1.1,
"notes": "Habitus daun mendatar menutup permukaan tanah, efektif menekan erosi percik hujan di gawangan."
},
"labor_mandays_per_ha": 105
},
"porang": {
"key": "porang",
"scientific_name": "Amorphophallus muelleri",
"common_name_id": "Porang / Iles-iles",
"common_name_en": "Elephant Foot Yam / Konjac",
"category_id": "Umbi Naungan Kanopi Lebat",
"category_en": "Deep Shade Sciophyte Tuber",
"palm_age_suitable_min": 7.0,
"palm_age_suitable_max": 20.0,
"shade_tolerance_pct": 60.0,
"optimal_par_umol": 550.0,
"optimal_soil_ph_min": 5.5,
"optimal_soil_ph_max": 6.8,
"preferred_soil_texture": "Porous berpasir bebas genangan air",
"growing_period_months": 7,
"population_per_ha_effective": 22000,
"fresh_yield_ton_ha_mono": 25.0,
"fresh_yield_ton_ha_intercrop": 14.0,
"farmgate_price_idr_kg": 8000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 50.0,
"mop_supplement_kg_ha": 83.3,
"profile": "Konsumen Kalium & Kalsium Tinggi"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 1.2,
"notes": "Mengoptimalkan lorong sawit tua bertajuk rapat (>7 thn). Memperbaiki aerasi tanah melalui perakaran umbi."
},
"labor_mandays_per_ha": 80
},
"cardamom": {
"key": "cardamom",
"scientific_name": "Amomum compactum",
"common_name_id": "Kapulaga Jawa",
"common_name_en": "Java Cardamom",
"category_id": "Rempah Naungan Lembap Rapat",
"category_en": "Extreme Shade Spices",
"palm_age_suitable_min": 8.0,
"palm_age_suitable_max": 25.0,
"shade_tolerance_pct": 70.0,
"optimal_par_umol": 450.0,
"optimal_soil_ph_min": 5.0,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Lembap kaya serasah organik",
"growing_period_months": 12,
"population_per_ha_effective": 3200,
"fresh_yield_ton_ha_mono": 3.0,
"fresh_yield_ton_ha_intercrop": 1.8,
"farmgate_price_idr_kg": 85000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 35.0,
"mop_supplement_kg_ha": 58.3,
"profile": "Kebutuhan Hara Moderat Humus"
},
"palm_impact": {
"rating": "Sangat Positif (++)",
"score": 1.4,
"notes": "Menyukai kelembapan tinggi di bawah kanopi sawit tua. Tidak bersaing karena perakaran serabut di serasah atas."
},
"labor_mandays_per_ha": 110
},
"vanilla": {
"key": "vanilla",
"scientific_name": "Vanilla planifolia",
"common_name_id": "Vanili Tropis",
"common_name_en": "Vanilla Orchid",
"category_id": "Anggrek Panjat Bernilai Tinggi",
"category_en": "Climbing Shade Orchids",
"palm_age_suitable_min": 6.0,
"palm_age_suitable_max": 18.0,
"shade_tolerance_pct": 50.0,
"optimal_par_umol": 600.0,
"optimal_soil_ph_min": 5.5,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Lapisan atas kaya humus tebal",
"growing_period_months": 36,
"population_per_ha_effective": 2000,
"fresh_yield_ton_ha_mono": 1.2,
"fresh_yield_ton_ha_intercrop": 0.7,
"farmgate_price_idr_kg": 150000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 20.0,
"mop_supplement_kg_ha": 33.3,
"profile": "Konsumen Bahan Organik Alami"
},
"palm_impact": {
"rating": "Sangat Positif (++)",
"score": 1.3,
"notes": "Menggunakan tiang panjat hidup mandiri di lorong gawangan (dilarang memanjat batang sawit langsung)."
},
"labor_mandays_per_ha": 180
},
"soybean": {
"key": "soybean",
"scientific_name": "Glycine max",
"common_name_id": "Kedelai Tropis (Dena-1)",
"common_name_en": "Shade-Tolerant Soybean",
"category_id": "Legum Butir (Fiksasi Nitrogen)",
"category_en": "Grain Legumes (N-Fixing)",
"palm_age_suitable_min": 1.0,
"palm_age_suitable_max": 3.5,
"shade_tolerance_pct": 20.0,
"optimal_par_umol": 1200.0,
"optimal_soil_ph_min": 5.5,
"optimal_soil_ph_max": 6.8,
"preferred_soil_texture": "Lempung berpasir subur",
"growing_period_months": 3,
"population_per_ha_effective": 160000,
"fresh_yield_ton_ha_mono": 2.6,
"fresh_yield_ton_ha_intercrop": 1.6,
"farmgate_price_idr_kg": 12000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 65.0,
"urea_saved_kg_ha": 141.3,
"k2o_supplement_kg_ha": 0.0,
"mop_supplement_kg_ha": 0.0,
"profile": "Fiksasi N Simbiotik (Rhizobium)"
},
"palm_impact": {
"rating": "Sangat Positif (++)",
"score": 1.5,
"notes": "Menyumbang nitrogen alami ke profil tanah. Menekan gulma alang-alang dan erosi pada sawit TBM."
},
"labor_mandays_per_ha": 45
},
"peanut": {
"key": "peanut",
"scientific_name": "Arachis hypogaea",
"common_name_id": "Kacang Tanah",
"common_name_en": "Groundnut / Peanut",
"category_id": "Legum Pangan (Fiksasi N)",
"category_en": "Grain Legumes (N-Fixing)",
"palm_age_suitable_min": 1.0,
"palm_age_suitable_max": 3.5,
"shade_tolerance_pct": 20.0,
"optimal_par_umol": 1150.0,
"optimal_soil_ph_min": 5.5,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Gembur remah berpasir",
"growing_period_months": 3.5,
"population_per_ha_effective": 140000,
"fresh_yield_ton_ha_mono": 2.2,
"fresh_yield_ton_ha_intercrop": 1.4,
"farmgate_price_idr_kg": 16000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 60.0,
"urea_saved_kg_ha": 130.4,
"k2o_supplement_kg_ha": 0.0,
"mop_supplement_kg_ha": 0.0,
"profile": "Fiksasi N Simbiotik (Bradyrhizobium)"
},
"palm_impact": {
"rating": "Sangat Positif (++)",
"score": 1.4,
"notes": "Menggemburkan tanah gawangan dan memasok residu daun legum kaya hara setelah panen."
},
"labor_mandays_per_ha": 50
},
"maize": {
"key": "maize",
"scientific_name": "Zea mays",
"common_name_id": "Jagung Hibrida",
"common_name_en": "Field Corn / Maize",
"category_id": "Serealia Pangan Penuh Cahaya",
"category_en": "Cereals & Food Staples",
"palm_age_suitable_min": 1.0,
"palm_age_suitable_max": 2.5,
"shade_tolerance_pct": 15.0,
"optimal_par_umol": 1400.0,
"optimal_soil_ph_min": 5.6,
"optimal_soil_ph_max": 7.0,
"preferred_soil_texture": "Lempung berpasir subur",
"growing_period_months": 3.5,
"population_per_ha_effective": 50000,
"fresh_yield_ton_ha_mono": 8.0,
"fresh_yield_ton_ha_intercrop": 4.5,
"farmgate_price_idr_kg": 5500.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 25.0,
"mop_supplement_kg_ha": 41.7,
"profile": "Konsumen Nitrogen & Fosfor Cepat"
},
"palm_impact": {
"rating": "Netral (0)",
"score": 0.0,
"notes": "Khusus TBM muda (<2.5 thn). Batang jagung jadi mulsa, tetapi butuh pemupukan N terpisah agar tidak berebut hara."
},
"labor_mandays_per_ha": 40
},
"sorghum": {
"key": "sorghum",
"scientific_name": "Sorghum bicolor",
"common_name_id": "Sorgum Manis",
"common_name_en": "Sweet Sorghum",
"category_id": "Serealia Tahan Kering (C4)",
"category_en": "Drought-Hardy Cereal",
"palm_age_suitable_min": 1.0,
"palm_age_suitable_max": 3.0,
"shade_tolerance_pct": 15.0,
"optimal_par_umol": 1350.0,
"optimal_soil_ph_min": 4.5,
"optimal_soil_ph_max": 7.0,
"preferred_soil_texture": "Toleran tanah masam dan marginal",
"growing_period_months": 3.5,
"population_per_ha_effective": 55000,
"fresh_yield_ton_ha_mono": 6.5,
"fresh_yield_ton_ha_intercrop": 3.5,
"farmgate_price_idr_kg": 6000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 20.0,
"mop_supplement_kg_ha": 33.3,
"profile": "Efisien Hara & Tahan Cekaman"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 0.8,
"notes": "Biomassa brangkasan tinggi sebagai pengisi rorak sedimen penahan limpasan air."
},
"labor_mandays_per_ha": 40
},
"sweet_potato": {
"key": "sweet_potato",
"scientific_name": "Ipomoea batatas",
"common_name_id": "Ubi Jalar",
"common_name_en": "Sweet Potato",
"category_id": "Umbi Penutup Tanah",
"category_en": "Ground-Cover Tuber",
"palm_age_suitable_min": 1.0,
"palm_age_suitable_max": 3.5,
"shade_tolerance_pct": 25.0,
"optimal_par_umol": 1100.0,
"optimal_soil_ph_min": 5.0,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Gembur berpasir remah",
"growing_period_months": 4,
"population_per_ha_effective": 30000,
"fresh_yield_ton_ha_mono": 18.0,
"fresh_yield_ton_ha_intercrop": 12.0,
"farmgate_price_idr_kg": 4000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 30.0,
"mop_supplement_kg_ha": 50.0,
"profile": "Konsumen Kalium Sedang"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 1.0,
"notes": "Tajuk merambat di permukaan tanah efektif sebagai cover crop penahan erosi dan penekan gulma."
},
"labor_mandays_per_ha": 65
},
"serai_wangi": {
"key": "serai_wangi",
"scientific_name": "Cymbopogon nardus",
"common_name_id": "Serai Wangi",
"common_name_en": "Citronella Grass",
"category_id": "Minyak Atsiri & Penolak Hama",
"category_en": "Bio-Repellent Essential Oil",
"palm_age_suitable_min": 4.0,
"palm_age_suitable_max": 12.0,
"shade_tolerance_pct": 35.0,
"optimal_par_umol": 800.0,
"optimal_soil_ph_min": 4.5,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Toleran tanah berlereng dan marginal",
"growing_period_months": 6,
"population_per_ha_effective": 16000,
"fresh_yield_ton_ha_mono": 16.0,
"fresh_yield_ton_ha_intercrop": 10.0,
"farmgate_price_idr_kg": 2500.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 15.0,
"mop_supplement_kg_ha": 25.0,
"profile": "Konsumen Hara Rendah"
},
"palm_impact": {
"rating": "Sangat Positif (++)",
"score": 1.5,
"notes": "Aroma minyak sitronelal alami menolak hama babi hutan, ulat api, dan tikus. Akarnya mengikat tanah lereng."
},
"labor_mandays_per_ha": 60
},
"patchouli": {
"key": "patchouli",
"scientific_name": "Pogostemon cablin",
"common_name_id": "Nilam Aceh",
"common_name_en": "Patchouli",
"category_id": "Minyak Atsiri Ekspor",
"category_en": "Export Essential Oil",
"palm_age_suitable_min": 4.0,
"palm_age_suitable_max": 8.0,
"shade_tolerance_pct": 35.0,
"optimal_par_umol": 850.0,
"optimal_soil_ph_min": 5.5,
"optimal_soil_ph_max": 6.5,
"preferred_soil_texture": "Kaya humus dengan drainase baik",
"growing_period_months": 6,
"population_per_ha_effective": 20000,
"fresh_yield_ton_ha_mono": 12.0,
"fresh_yield_ton_ha_intercrop": 7.0,
"farmgate_price_idr_kg": 6500.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 30.0,
"mop_supplement_kg_ha": 50.0,
"profile": "Kebutuhan Hara Moderat"
},
"palm_impact": {
"rating": "Positif (+)",
"score": 1.1,
"notes": "Daun disuling menghasilkan minyak atsiri bernilai ekspor tinggi. Residu sulingan dikembalikan sebagai kompos."
},
"labor_mandays_per_ha": 75
},
"coffee": {
"key": "coffee",
"scientific_name": "Coffea canephora",
"common_name_id": "Kopi Robusta Naungan",
"common_name_en": "Shade Robusta Coffee",
"category_id": "Perkebunan Sela Menahun",
"category_en": "Perennial Shade Crop",
"palm_age_suitable_min": 8.0,
"palm_age_suitable_max": 20.0,
"shade_tolerance_pct": 45.0,
"optimal_par_umol": 650.0,
"optimal_soil_ph_min": 4.5,
"optimal_soil_ph_max": 6.2,
"preferred_soil_texture": "Solum tanah dalam subur",
"growing_period_months": 24,
"population_per_ha_effective": 1200,
"fresh_yield_ton_ha_mono": 1.5,
"fresh_yield_ton_ha_intercrop": 0.9,
"farmgate_price_idr_kg": 45000.0,
"nutrient_demand": {
"n_fixation_kg_ha": 0.0,
"urea_saved_kg_ha": 0.0,
"k2o_supplement_kg_ha": 35.0,
"mop_supplement_kg_ha": 58.3,
"profile": "Konsumen Kalium & Nitrogen Seimbang"
},
"palm_impact": {
"rating": "Netral (0)",
"score": 0.0,
"notes": "Wajib pemangkasan bentuk teratur di lorong mati dan menjaga radius 2.0m piringan sawit tetap steril."
},
"labor_mandays_per_ha": 130
}
}

def get_crop_profile(crop_key: str) -> Dict[str, Any]:
    """Mencari profil lengkap komoditas berdasarkan kunci atau pencocokan teks."""
    q = (crop_key or "").lower().strip()
    if q in CROPS_DATABASE:
        return CROPS_DATABASE[q]
    for k, v in CROPS_DATABASE.items():
        if (q in k or
            q in v["common_name_id"].lower() or
            q in v["common_name_en"].lower() or
            q in v["scientific_name"].lower()):
            return v
    return CROPS_DATABASE["red_ginger"]


def list_all_companion_crops() -> List[Dict[str, Any]]:
    """Mengembalikan daftar seluruh komoditas tanaman sela dalam database."""
    return list(CROPS_DATABASE.values())


def evaluate_crop_suitability(crop_key: str, palm_age: float, soil_ph: float, slope: float, elevation: float) -> Dict[str, Any]:
    """Menghitung persentase korelasi jenis tanah, umur sawit, dan kelerengan untuk satu tanaman."""
    crop = get_crop_profile(crop_key)

    # 1. Skor Umur Sawit & Radiasi PAR (0 - 100)
    age_min = crop["palm_age_suitable_min"]
    age_max = crop["palm_age_suitable_max"]
    if age_min <= palm_age <= age_max:
        age_score = 98.0
    elif palm_age < age_min:
        diff = age_min - palm_age
        age_score = max(20.0, 95.0 - (diff * 22.0))
    else:
        diff = palm_age - age_max
        age_score = max(20.0, 95.0 - (diff * 12.0))

    # 2. Skor Kimia Tanah / pH (0 - 100)
    ph_min = crop["optimal_soil_ph_min"]
    ph_max = crop["optimal_soil_ph_max"]
    if ph_min <= soil_ph <= ph_max:
        soil_score = 96.0
    else:
        diff = min(abs(soil_ph - ph_min), abs(soil_ph - ph_max))
        soil_score = max(25.0, 95.0 - (diff * 35.0))

    # 3. Skor Kelerengan Lereng (0 - 100)
    if slope <= 8.0:
        slope_score = 98.0
    elif slope <= 15.0:
        slope_score = 82.0
    else:
        slope_score = 55.0

    # Total Skor Kesesuaian Terbobot
    total_suitability = round((age_score * 0.45) + (soil_score * 0.35) + (slope_score * 0.20), 1)

    # Hitung rasio kesetaraan lahan parsial tanaman (PLER Crop)
    pler_crop = round(crop["fresh_yield_ton_ha_intercrop"] / crop["fresh_yield_ton_ha_mono"], 4)
    # Asumsi PLER sawit adalah 0.95 (defisit TBS minimal di bawah 5%)
    projected_ler = round(0.9545 + pler_crop, 4)

    gross_rev_idr = crop["fresh_yield_ton_ha_intercrop"] * 1000.0 * crop["farmgate_price_idr_kg"]

    return {
        "crop": crop,
        "total_suitability": total_suitability,
        "soil_correlation_pct": round(soil_score, 1),
        "age_suitability_pct": round(age_score, 1),
        "slope_suitability_pct": round(slope_score, 1),
        "projected_ler": projected_ler,
        "gross_revenue_idr_ha": gross_rev_idr
    }


def evaluate_multi_crops_combination(
    selected_keys: List[str],
    palm_age: float,
    land_area: float,
    soil_ph: float = 5.5,
    slope: float = 4.5,
    elevation: float = 142.0
) -> Dict[str, Any]:
    """
    Menghitung akumulasi komprehensif untuk kombinasi 1 sampai 3 tanaman sela:
    - Alokasi proporsional lorong gawangan
    - Akumulasi LER polikultur
    - Hutan terselamatkan (Avoided Deforestation Ha)
    - Neraca NPK bersih
    - Total pendapatan kotor
    - Indeks dampak sinergi ke tanaman sawit
    """
    valid_keys = [k for k in selected_keys if k in CROPS_DATABASE][:3]
    if not valid_keys:
        valid_keys = ["red_ginger"]

    n = len(valid_keys)
    # Pembobotan proporsi lorong aktif (3.79m)
    if n == 1:
        weights = [1.0]
    elif n == 2:
        weights = [0.5, 0.5]
    else:
        weights = [0.4, 0.3, 0.3]

    eval_items = []
    combined_pler_crop = 0.0
    total_urea_saved_kg = 0.0
    total_mop_demand_kg = 0.0
    total_revenue_idr = 0.0
    weighted_impact_score = 0.0

    # Efektif area lorong tumpang sari (82.91% dari total luas Ha di luar piringan 2m)
    effective_corridor_area_ha = land_area * 0.8291

    for idx, key in enumerate(valid_keys):
        w = weights[idx]
        item = evaluate_crop_suitability(key, palm_age, soil_ph, slope, elevation)
        crop_data = item["crop"]
        
        pler_individual = crop_data["fresh_yield_ton_ha_intercrop"] / crop_data["fresh_yield_ton_ha_mono"]
        combined_pler_crop += (w * pler_individual)
        
        # Neraca pupuk terbobot
        total_urea_saved_kg += (w * crop_data["nutrient_demand"]["urea_saved_kg_ha"] * effective_corridor_area_ha)
        total_mop_demand_kg += (w * crop_data["nutrient_demand"]["mop_supplement_kg_ha"] * effective_corridor_area_ha)
        
        # Omzet terbobot
        crop_rev = (effective_corridor_area_ha * w * crop_data["fresh_yield_ton_ha_intercrop"] * 1000.0 * crop_data["farmgate_price_idr_kg"])
        total_revenue_idr += crop_rev

        # Skor dampak ke sawit
        weighted_impact_score += (w * crop_data["palm_impact"]["score"])

        eval_items.append({
            "key": key,
            "crop": crop_data,
            "weight_pct": round(w * 100, 0),
            "suitability_score": item["total_suitability"],
            "projected_ler": item["projected_ler"],
            "revenue_share_idr": crop_rev
        })

    # PLER Sawit baku (95.45% asumsi panen TBS stabil)
    pler_palm = 0.9545
    combined_ler = round(pler_palm + combined_pler_crop, 4)
    pls_percentage = round((1.0 - (1.0 / combined_ler)) * 100.0, 2) if combined_ler > 1.0 else 0.0
    spared_forest_ha = round(land_area * (combined_ler - 1.0), 2) if combined_ler > 1.0 else 0.0
    carbon_tco2e = round((spared_forest_ha * 450.0) + (land_area * 1.8), 2)

    # Label sinergi kelapa sawit
    if weighted_impact_score >= 1.3:
        impact_verdict = "Sangat Positif (++) - Sinergis & Bio-Protektif"
    elif weighted_impact_score >= 0.8:
        impact_verdict = "Positif (+) - Aman Tanpa Defisit TBS"
    else:
        impact_verdict = "Netral (0) - Memerlukan Pemantauan Hara Ketat"

    return {
        "selected_crops": eval_items,
        "combined_ler": combined_ler,
        "land_spared_pct": pls_percentage,
        "forest_spared_ha": spared_forest_ha,
        "carbon_benefit_tco2e": carbon_tco2e,
        "net_urea_saved_kg": round(total_urea_saved_kg, 1),
        "net_mop_supplement_kg": round(total_mop_demand_kg, 1),
        "total_projected_revenue_idr": round(total_revenue_idr, 0),
        "palm_synergy_verdict": impact_verdict,
        "weighted_impact_score": round(weighted_impact_score, 2)
    }