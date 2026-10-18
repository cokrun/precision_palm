# kalkulasi/biofisika.py
"""
Modul Biofisika, Dinamika Radiasi Kanopi, dan Geometri Spasial Kelapa Sawit.
Mengimplementasikan:
1. Model Pertumbuhan Sigmoidal Logistik Indeks Luas Daun (LAI).
2. Hukum Atenuasi Radiasi Beer-Lambert (Monsi & Saeki, 1953; k = 0.45).
3. Geometri Spasial Tajuk & Preservasi Piringan Steril Radius 2.0m (PPKS GAP).
"""

import math
from typing import Dict, Any

def calculate_leaf_area_index(
    palm_age_years: float,
    lai_max: float = 5.5,
    growth_rate: float = 0.7,
    t0_inflection: float = 3.5
) -> float:
    """
    Menghitung Indeks Luas Daun (Leaf Area Index / LAI) kelapa sawit berdasarkan model sigmoidal logistik.
    Formula: LAI(t) = LAI_max / (1 + exp(-r * (t - t0)))
    """
    if palm_age_years < 0:
        raise ValueError("Umur kelapa sawit tidak boleh bernilai negatif.")
    return lai_max / (1.0 + math.exp(-growth_rate * (palm_age_years - t0_inflection)))

def calculate_beer_lambert_transmission(
    lai: float,
    i0_par: float = 1800.0,
    k_extinction: float = 0.45
) -> Dict[str, float]:
    """
    Menghitung penetrasi radiasi fotosintesis aktif (PAR) menembus tajuk sawit via Hukum Beer-Lambert.
    Formula: I = I_0 * exp(-k * LAI)
    """
    if lai < 0:
        raise ValueError("Nilai LAI tidak boleh bernilai negatif.")
    if i0_par < 0 or k_extinction < 0:
        raise ValueError("Nilai I0 PAR dan koefisien ekstingsi k tidak boleh negatif.")

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
    """Menghitung metrik transmisi kanopi berdasarkan umur pohon sawit."""
    lai = calculate_leaf_area_index(palm_age_years=palm_age_years)
    rad_metrics = calculate_beer_lambert_transmission(lai=lai, i0_par=i0_par, k_extinction=k_extinction)
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
    """
    Menghitung geometri spasial tajuk dan preservasi piringan steril radius 2.0 meter (GAP PPKS).
    Akar aktif serap hara sawit terkonsentrasi di radius 0-2.0 meter dari pokok (zona larangan olah tanah).
    """
    if palm_age_years < 0:
        raise ValueError("Umur kelapa sawit tidak boleh bernilai negatif.")
    if planting_density <= 0:
        raise ValueError("Kerapatan tanam kelapa sawit harus lebih besar dari 0.")

    # Radius pelepah daun terpanjang
    frond_radius = 5.5 / (1.0 + math.exp(-0.6 * (palm_age_years - 3.5)))
    canopy_area_per_ha = planting_density * math.pi * (frond_radius ** 2)
    canopy_fraction = min(1.0, canopy_area_per_ha / 10000.0)
    canopy_cover_percentage = round(canopy_fraction * 100.0, 2)

    # Buffer piringan steril radius 2.0m di sekeliling pokok
    buffer_radius_m = 2.0
    buffer_area_per_ha = planting_density * math.pi * (buffer_radius_m ** 2)
    buffer_fraction = buffer_area_per_ha / 10000.0
    unplanted_buffer_percentage = round(buffer_fraction * 100.0, 2)
    net_effective_percentage = round((1.0 - buffer_fraction) * 100.0, 2)

    # Koridor bersih efektif pada pola tanam segitiga 9.0m x 9.0m
    effective_corridor_width_m = round(max(1.5, 9.0 - (2.0 * buffer_radius_m)), 2)

    return {
        "frond_radius_m": round(frond_radius, 2),
        "canopy_cover_pct": canopy_cover_percentage,
        "effective_intercrop_area_pct": net_effective_percentage,
        "unplanted_buffer_pct": unplanted_buffer_percentage,
        "sterile_ring_radius_m": buffer_radius_m,
        "effective_corridor_width_m": effective_corridor_width_m
    }