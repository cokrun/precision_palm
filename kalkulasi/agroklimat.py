# kalkulasi/agroklimat.py
"""
Modul Evaluasi Agroklimat, Topografi, dan Edafik Kelapa Sawit.
Merujuk pada Standar Teknis PPKS, FAO (Djaenudin et al., 2011), dan Corley & Tinker (2016):
1. Kesesuaian Ketinggian Tempat (Elevasi & Environmental Lapse Rate 0.6°C / 100m).
2. Kemiringan Lereng (Topografi & Konservasi Rorak / Teras Kontur).
3. Dinamika Curah Hujan & Model Lag Penurunan TBS Akibat Defisit Air (12-24 Bulan).
4. Penyangga Iklim Mikro Gawangan Sela (Microclimate Buffering).
5. Evaluasi Stres Fisiologis Stomata (Suhu & Kelembapan RH).
"""

import math
from typing import Dict, Any

def calculate_elevation_suitability(
    elevation_m: float,
    sea_level_temperature_c: float = 28.5
) -> Dict[str, Any]:
    """
    Evaluasi ketinggian tempat berdasarkan baku mutu agronomi PPKS:
    - S1: 0 - 400 m dpl (Optimal)
    - S2: 400 - 500 m dpl (Cukup Sesuai)
    - S3: 500 - 600 m dpl (Marginal)
    - N: > 600 m dpl (Tidak Sesuai - Lapse rate memicu hambatan metabolisme)
    """
    if elevation_m < 0:
        raise ValueError("Nilai ketinggian tempat tidak boleh negatif.")

    temp_drop = (elevation_m / 100.0) * 0.6
    estimated_temp_c = round(max(15.0, sea_level_temperature_c - temp_drop), 1)

    if elevation_m <= 400.0:
        suitability_class = "S1"
        frond_production_rate = "20 - 24 pelepah/tahun (Optimal)"
        score = 100.0
        desc_id = f"Elevasi optimal ({elevation_m:.0f} m dpl <= 400 m): Dataran rendah tropis ideal. Suhu rerata {estimated_temp_c}°C mendukung diferensiasi tandan dan inisiasi pelepah normal."
        desc_en = f"Optimal elevation ({elevation_m:.0f} m ASL <= 400 m): Ideal lowland tropics. Mean temp {estimated_temp_c}°C supports standard bunch development and frond initiation."
    elif elevation_m <= 500.0:
        suitability_class = "S2"
        frond_production_rate = "18 - 20 pelepah/tahun (Sedang)"
        score = 80.0
        desc_id = f"Elevasi cukup sesuai ({elevation_m:.0f} m dpl): Suhu sejuk malam hari mulai memperlambat laju inisiasi pelepah."
        desc_en = f"Moderately suitable elevation ({elevation_m:.0f} m ASL): Cooler night temperatures depress frond emergence rate."
    elif elevation_m <= 600.0:
        suitability_class = "S3"
        frond_production_rate = "15 - 18 pelepah/tahun (Marginal)"
        score = 60.0
        desc_id = f"Elevasi marginal ({elevation_m:.0f} m dpl): Pematangan TBS melambat, rasio bunga jantan meningkat."
        desc_en = f"Marginally suitable elevation ({elevation_m:.0f} m ASL): Slower bunch ripening, higher male sex ratio."
    else:
        suitability_class = "N"
        frond_production_rate = "< 15 pelepah/tahun (Terhambat)"
        score = 35.0
        desc_id = f"Elevasi tidak sesuai ({elevation_m:.0f} m dpl > 600 m): Pembatas agronomis berat. Suhu rendah menekan metabolisme."
        desc_en = f"Unsuitable elevation ({elevation_m:.0f} m ASL > 600 m): Severe limitation. Cool temperatures suppress metabolism."

    return {
        "elevation_m": elevation_m,
        "suitability_class": suitability_class,
        "score": score,
        "estimated_ambient_temperature_c": estimated_temp_c,
        "annual_frond_production_capacity": frond_production_rate,
        "advisory_description_id": desc_id,
        "advisory_description_en": desc_en
    }

def calculate_slope_suitability(slope_degrees: float) -> Dict[str, Any]:
    """
    Evaluasi kemiringan lereng (topografi) merujuk pada standar PPKS dan konservasi tanah:
    - 0° - 4.5° (0 - 8%): S1 (Datar/Landai - Bebas olah tanah)
    - 4.5° - 12° (8 - 21%): S2 (Berombak/Bergelombang - Wajib rorak & tapak timbun)
    - 12° - 16° (21 - 30%): S3 (Berbukit - Wajib teras kontur bersambung)
    - > 16° (> 30%): N (Terjal - Pembatas berat, rentan erosi parah)
    """
    if slope_degrees < 0:
        raise ValueError("Sudut kemiringan lereng tidak boleh negatif.")

    slope_pct = round(math.tan(math.radians(slope_degrees)) * 100.0, 1)

    if slope_degrees <= 4.5:
        suitability = "S1"
        score = 100.0
        conservation_id = "Topografi datar/landai. Bebas olah tanah mekanis; resiko erosi sangat rendah."
        conservation_en = "Flat to gently undulating. Low erosion hazard; standard soil conservation practices."
    elif slope_degrees <= 12.0:
        suitability = "S2"
        score = 80.0
        conservation_id = "Topografi berombak/bergelombang. Wajib rorak penampung sedimen, tapak timbun, dan barisan sela sejajar kontur."
        conservation_en = "Undulating to rolling terrain. Silt pits (rorak), individual planting platforms, and contour alleys required."
    elif slope_degrees <= 16.0:
        suitability = "S3"
        score = 60.0
        conservation_id = "Topografi berbukit curam. Wajib teras kontur bersambung (contour terraces) dan benteng vegetasi penahan erosi."
        conservation_en = "Hilly terrain. Continuous contour terraces and vegetative barrier hedgerows required."
    else:
        suitability = "N"
        score = 30.0
        conservation_id = "Topografi terjal (>16° / >30%). Pembatas berat budidaya sawit. Rawan longsor dan pencucian hara pupuk permukaan."
        conservation_en = "Steep terrain (>16° / >30%). Severe limitation. Severe erosion, runoff leaching, and landslide vulnerability."

    return {
        "slope_degrees": slope_degrees,
        "slope_pct": slope_pct,
        "suitability_class": suitability,
        "score": score,
        "conservation_recommendation_id": conservation_id,
        "conservation_recommendation_en": conservation_en
    }

def calculate_water_deficit_and_yield_impact(annual_rainfall_mm: float) -> Dict[str, Any]:
    """
    Menghitung defisit air tahunan (< 1.500 mm/tahun) dan proyeksi lag phase 12-24 bulan
    penurunan TBS sawit menurut model fenologi Corley & Tinker (2016).
    """
    if annual_rainfall_mm < 1500.0:
        water_deficit_mm = round(1500.0 - annual_rainfall_mm, 1)
        severity = "MODERATE" if water_deficit_mm < 300.0 else ("SEVERE" if water_deficit_mm < 600.0 else "EXTREME")
        tbs_reduction_pct = min(45.0, round((water_deficit_mm / 1500.0) * 100.0 * 0.85, 1))
        female_flower_abortion_pct = min(40.0, round((water_deficit_mm / 1500.0) * 100.0 * 0.70, 1))
        desc_id = (
            f"Defisit Air Terdeteksi ({annual_rainfall_mm:.1f} mm/thn < 1.500 mm; defisit {water_deficit_mm:.1f} mm). "
            f"Memicu aborsi bunga betina +{female_flower_abortion_pct}% dan penurunan produksi TBS sebesar {tbs_reduction_pct}% "
            "pada siklus lag 12–24 bulan ke depan."
        )
        desc_en = (
            f"Water Deficit ({annual_rainfall_mm:.1f} mm/yr < 1,500 mm; deficit {water_deficit_mm:.1f} mm). "
            f"Induces +{female_flower_abortion_pct}% female flower abortion and {tbs_reduction_pct}% FFB yield suppression "
            "over the forward 12–24 months lag cycle."
        )
    else:
        water_deficit_mm = 0.0
        severity = "NONE"
        tbs_reduction_pct = 0.0
        female_flower_abortion_pct = 0.0
        desc_id = f"Curah hujan optimal ({annual_rainfall_mm:.1f} mm/tahun >= 1.500 mm). Diferensiasi primordia bunga normal."
        desc_en = f"Optimal rainfall ({annual_rainfall_mm:.1f} mm/year >= 1,500 mm). Inflorescence sex differentiation normal."

    return {
        "annual_rainfall_mm": annual_rainfall_mm,
        "water_deficit_mm": water_deficit_mm,
        "deficit_severity": severity,
        "tbs_yield_reduction_projected_pct": tbs_reduction_pct,
        "female_flower_abortion_projected_pct": female_flower_abortion_pct,
        "impact_timeline_months": "12-24",
        "advisory_description_id": desc_id,
        "advisory_description_en": desc_en
    }

def calculate_microclimate_buffering(
    intercrop_canopy_cover_pct: float = 65.0
) -> Dict[str, Any]:
    """
    Menghitung penyangga iklim mikro di lorong gawangan sela:
    - Penurunan suhu tanah: 2.0°C - 4.0°C.
    - Penurunan evaporasi air tanah: 25% - 35%.
    """
    cov_ratio = max(0.0, min(1.0, intercrop_canopy_cover_pct / 100.0))
    soil_evap_reduction_pct = round(25.0 + (cov_ratio * 10.0), 1)
    soil_temp_reduction_c = round(2.0 + (cov_ratio * 2.0), 1)
    moisture_retention_gain_pct = round(15.0 + (cov_ratio * 15.0), 1)

    return {
        "intercrop_canopy_cover_pct": intercrop_canopy_cover_pct,
        "soil_evaporation_reduction_pct": soil_evap_reduction_pct,
        "soil_temperature_reduction_c": soil_temp_reduction_c,
        "moisture_retention_gain_pct": moisture_retention_gain_pct,
        "buffering_status": "ACTIVE_BUFFERING"
    }

def evaluate_temperature_humidity_stress(
    mean_temperature_c: float,
    relative_humidity_pct: float
) -> Dict[str, Any]:
    """Mengevaluasi kesesuaian suhu (24-28°C) dan kelembapan (70-90%) untuk mencegah penutupan stomata dini."""
    temp_optimal = 24.0 <= mean_temperature_c <= 28.0
    rh_optimal = 70.0 <= relative_humidity_pct <= 90.0
    is_stress = not (temp_optimal and rh_optimal)

    return {
        "mean_temperature_c": mean_temperature_c,
        "relative_humidity_pct": relative_humidity_pct,
        "is_stomata_stress": is_stress,
        "temperature_optimal": temp_optimal,
        "humidity_optimal": rh_optimal
    }