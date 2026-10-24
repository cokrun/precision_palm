import unittest
import hashlib
import json
import math
import os
import sqlite3
import tempfile
from unittest.mock import Mock, patch

import app as app_module
import database as database_module
from kalkulasi.engine import calculate_crop_yield_scenario, resolve_crop_yield_benchmark


class TestSimulationEvidenceLink(unittest.TestCase):
    def test_yield_reference_provenance_is_verified_and_kept_scenario_only(self):
        age = 7.5
        reference = calculate_crop_yield_scenario(age, "Red Ginger (Zingiber officinale var. rubrum)")
        data = {"yield_reference": {
            "source": "CLIENT_GENERATED_SCENARIO_REFERENCE",
            "model": reference["model"],
            "model_version": reference["model_version"],
            "crop_key": "red_ginger",
        }}
        expected = {
            "yield_palm_inter": reference["yield_palm_inter"],
            "yield_palm_mono": reference["yield_palm_mono"],
            "yield_crop_inter": reference["yield_crop_inter"],
            "yield_crop_mono": reference["yield_crop_mono"],
        }
        inputs = {"palm_age": age, "crop_name": "Red Ginger (Zingiber officinale var. rubrum)", **expected}

        provenance = app_module._yield_input_provenance(data, inputs)
        self.assertEqual(provenance["source"], "CLIENT_GENERATED_SCENARIO_REFERENCE")
        self.assertEqual(provenance["status"], "SCENARIO_PROJECTION")
        self.assertEqual(provenance["model"], "logistic_age_crop_benchmark")
        self.assertEqual(provenance["model_version"], "2")
        self.assertFalse(provenance["field_measurement_verified"])

        inputs["yield_crop_inter"] += 1
        downgraded = app_module._yield_input_provenance(data, inputs)
        self.assertEqual(downgraded["source"], "USER_PROVIDED_UNVERIFIED")

    def test_crop_benchmarks_normalize_aliases_for_all_catalog_crops_and_cacao(self):
        crop_names = {
            "red_ginger": "Red Ginger (Zingiber officinale var. rubrum)",
            "cacao": "Shade Cacao (Theobroma cacao)",
            "coffee": "Shade Robusta Coffee (Coffea canephora)",
            "porang": "Konjac Tuber / Porang (Amorphophallus muelleri)",
            "cardamom": "Java Cardamom (Amomum compactum)",
            "turmeric": "Turmeric (Curcuma longa)",
            "patchouli": "Patchouli (Pogostemon cablin)",
            "soybean": "Shade Soybean (Glycine max / Dena-1)",
            "corn": "Field Corn (Zea mays)",
            "vanilla": "Vanilla Orchid (Vanilla planifolia)",
            "curcuma": "Javanese Turmeric / Temulawak (Curcuma zanthorrhiza)",
            "kencur": "Aromatic Ginger (Kaempferia galanga)",
            "peanut": "Groundnut (Arachis hypogaea)",
            "sorghum": "Sweet Sorghum (Sorghum bicolor)",
            "sweet_potato": "Sweet Potato (Ipomoea batatas)",
            "serai_wangi": "Citronella Grass (Cymbopogon nardus)",
        }

        for expected_key, display_name in crop_names.items():
            with self.subTest(crop=display_name):
                benchmark = resolve_crop_yield_benchmark(display_name)
                self.assertEqual(benchmark["crop_key"], expected_key)
                reference = calculate_crop_yield_scenario(7.5, display_name)
                self.assertTrue(all(reference[field] > 0 for field in (
                    "yield_palm_inter", "yield_palm_mono", "yield_crop_inter", "yield_crop_mono"
                )))

        self.assertEqual(resolve_crop_yield_benchmark("cocoa")["crop_key"], "cacao")
        self.assertEqual(resolve_crop_yield_benchmark("(Theobroma cacao)")["crop_key"], "cacao")
        self.assertEqual(resolve_crop_yield_benchmark("(Pogostemon cablin)")["crop_key"], "patchouli")
        self.assertEqual(resolve_crop_yield_benchmark("Nilam Aceh")["crop_key"], "patchouli")
        self.assertEqual(resolve_crop_yield_benchmark("unlisted crop")["crop_key"], "default")

    def test_cacao_yield_scenario_populates_preview_metrics(self):
        reference = calculate_crop_yield_scenario(7.5, "Shade Cacao (Theobroma cacao)")
        provenance = app_module._yield_input_provenance(
            {
                "yield_reference": {
                    "source": "CLIENT_GENERATED_SCENARIO_REFERENCE",
                    "model": reference["model"],
                    "model_version": reference["model_version"],
                    "crop_key": reference["crop_key"],
                }
            },
            {
                "palm_age": 7.5,
                "crop_name": "Shade Cacao (Theobroma cacao)",
                **{
                    field: reference[field]
                    for field in (
                        "yield_palm_inter",
                        "yield_palm_mono",
                        "yield_crop_inter",
                        "yield_crop_mono",
                    )
                },
            },
        )
        self.assertEqual(provenance["source"], "CLIENT_GENERATED_SCENARIO_REFERENCE")
        self.assertEqual(provenance["crop_key"], "cacao")

        response = app_module.app.test_client().post(
            "/api/simulate/compute",
            json={
                "kode_kebun": "EST-MDN-010",
                "palm_age": 7.5,
                "land_area": 50,
                "crop_name": "Shade Cacao (Theobroma cacao)",
                **{
                    field: reference[field]
                    for field in (
                        "yield_palm_inter",
                        "yield_palm_mono",
                        "yield_crop_inter",
                        "yield_crop_mono",
                    )
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["missing_inputs"], [])
        self.assertIsNotNone(response.json["data_numerik"]["efisiensi_lahan_ler"])
        self.assertIsNotNone(response.json["data_numerik"]["dampak_lingkungan_dan_karbon"])
        self.assertEqual(response.json["metric_statuses"]["avoided_land"], "SCENARIO_PROJECTION")

    def test_simulation_keeps_active_photo_and_vision_result_in_telemetry(self):
        image_url = "/api/media/evidence/EV-TEST-1"
        vision_summary = {
            "detection_badge": "2 saved detections",
            "evidence_id": "EV-TEST-1",
            "image_url": image_url,
            "filename": "evidence.jpg",
            "is_processed": True,
            "detected_entities": [
                {"label": "oil_palm", "box_2d": [100, 100, 300, 300]},
                {"label": "fruit_bunch", "box_2d": [400, 400, 600, 600]},
            ],
            "root_zone_compliance": "Not assessed by this image scan",
        }
        ai_reasoning = {
            "mode": "LOCAL_PREVIEW",
            "is_fallback": True,
            "verdict": "REQUIRES_FIELD_REVIEW",
            "audit_notice": "Gemini quota is exhausted.",
        }
        store = {"simulator_history": []}
        save_record = Mock(return_value={
            "record_id": 90399,
            "sha256": "A" * 64,
            "committed_at": "2026-10-24T16:08:37Z",
            "cloud_sync_status": "NOT_CONFIGURED",
            "idempotent_replay": False,
        })

        with patch.object(app_module, "save_simulation_record", save_record), patch.object(
            app_module, "read_local_store", return_value=store
        ), patch.object(app_module, "save_local_store"), patch.object(
            app_module, "record_unified_ai_log"
        ):
            response = app_module.app.test_client().post(
                "/api/simulate",
                headers={"Idempotency-Key": "sim-test-key-00000001"},
                json={
                    "kode_kebun": "EST-MDN-010",
                    "palm_age": 7.5,
                    "land_area": 50,
                    "crop_name": "Red Ginger",
                    "yield_palm_inter": 20.0,
                    "yield_palm_mono": 22.0,
                    "yield_crop_inter": 6.0,
                    "yield_crop_mono": 12.0,
                    "image_sample": image_url,
                    "photo_urls": [image_url],
                    "vision_summary": vision_summary,
                    "ai_reasoning": ai_reasoning,
                    "engine_mode": "AUTONOMOUS_STATUTORY_RULE_ENGINE",
                    "status_message": ai_reasoning["audit_notice"],
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["commit_status"], "COMMITTED")
        self.assertEqual(response.json["ledger"]["authority"], "LOCAL_SQLITE")
        self.assertEqual(response.json["ledger"]["sha256"], "A" * 64)
        save_record.assert_called_once()
        self.assertEqual(save_record.call_args.kwargs["image_path"], image_url)
        self.assertEqual(save_record.call_args.kwargs["photo_urls"], [image_url])
        self.assertEqual(save_record.call_args.kwargs["vision_summary"], vision_summary)
        self.assertEqual(save_record.call_args.kwargs["ai_reasoning"], ai_reasoning)
        self.assertEqual(save_record.call_args.kwargs["calculation_inputs"]["yield_palm_inter"], 20.0)
        self.assertIn("efisiensi_lahan_ler", save_record.call_args.kwargs["data_numerik"])
        saved_record = store["simulator_history"][0]
        self.assertEqual(saved_record["image_sample"], image_url)
        self.assertEqual(saved_record["photo_urls"], [image_url])
        self.assertEqual(saved_record["vision_summary"]["evidence_id"], "EV-TEST-1")
        self.assertEqual(saved_record["vision_summary"]["detected_entities"], vision_summary["detected_entities"])
        self.assertEqual(saved_record["ai_reasoning"]["mode"], "LOCAL_PREVIEW")
        self.assertEqual(saved_record["engine_mode"], "AUTONOMOUS_STATUTORY_RULE_ENGINE")
        self.assertEqual(saved_record["yield_input_provenance"]["source"], "USER_PROVIDED_UNVERIFIED")
        self.assertFalse(saved_record["yield_input_provenance"]["field_measurement_verified"])
        self.assertEqual(
            save_record.call_args.kwargs["canonical_snapshot"]["calculation"]["yield_input_provenance"]["status"],
            "SCENARIO_PROJECTION",
        )
        self.assertEqual(
            save_record.call_args.kwargs["canonical_snapshot"]["calculation"]["metric_statuses"]["biocircularity"],
            "SCENARIO_PROJECTION",
        )
        self.assertEqual(
            save_record.call_args.kwargs["canonical_snapshot"]["assumptions"]["biocircularity_status"],
            "SCENARIO_PROJECTION",
        )

    def test_preview_calculates_profile_metrics_without_measured_yields(self):
        response = app_module.app.test_client().post(
            "/api/simulate/compute",
            json={"kode_kebun": "EST-MDN-010"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["success"])
        self.assertEqual(response.json["calculation_engine"], "kalkulasi.engine")
        self.assertTrue(response.json["data_numerik"]["analisis_cahaya_kanopi"])
        self.assertTrue(response.json["data_numerik"]["geometri_kanopi_spasial"])
        self.assertTrue(response.json["data_numerik"]["kesesuaian_bioklimat_dan_tanah"])
        self.assertIsNone(response.json["data_numerik"]["efisiensi_lahan_ler"])
        self.assertIsNone(response.json["data_numerik"]["dampak_lingkungan_dan_karbon"])
        self.assertEqual(len(response.json["missing_inputs"]), 4)

    def test_preview_adds_yield_dependent_metrics_with_unverified_user_inputs(self):
        response = app_module.app.test_client().post(
            "/api/simulate/compute",
            json={
                "kode_kebun": "EST-MDN-010",
                "palm_age": 7.5,
                "land_area": 50,
                "yield_palm_inter": 20,
                "yield_palm_mono": 22,
                "yield_crop_inter": 6,
                "yield_crop_mono": 12,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["missing_inputs"], [])
        self.assertIsNotNone(response.json["data_numerik"]["efisiensi_lahan_ler"])
        self.assertIsNotNone(response.json["data_numerik"]["dampak_lingkungan_dan_karbon"])
        self.assertIsNotNone(response.json["data_numerik"]["neraca_hara_npk"])
        metrics = response.json["data_numerik"]
        avoided = metrics["dampak_lingkungan_dan_karbon"]["avoided_land_ha"]
        self.assertEqual(avoided, 20.45)
        self.assertEqual(avoided, metrics["komparasi_efisiensi_lahan"]["land_saved_ha"])
        self.assertEqual(
            metrics["dampak_lingkungan_dan_karbon"]["total_climate_benefit_tco2e"],
            round(avoided * 450.0 + 50 * 1.8, 2),
        )
        self.assertEqual(
            metrics["dampak_lingkungan_dan_karbon"]["status"],
            "SCENARIO_PROJECTION",
        )
        self.assertEqual(response.json["metric_statuses"]["yield_inputs"], "SCENARIO_PROJECTION")
        self.assertEqual(
            metrics["dampak_lingkungan_dan_karbon"]["eudr_article_9_status"],
            "NOT_ASSESSED",
        )
        self.assertEqual(response.json["data_numerik"]["analisis_cahaya_kanopi"]["leaf_area_index"], 5.18)
        self.assertEqual(response.json["metric_statuses"]["ler"], "DETERMINISTIC_MODEL")

    def test_preview_returns_biophysical_scenarios_and_carbon_price_valuation(self):
        with patch.object(app_module, "get_app_setting", return_value="15.5"):
            response = app_module.app.test_client().post(
                "/api/simulate/compute",
                json={
                    "kode_kebun": "EST-MDN-010",
                    "palm_age": 7.5,
                    "land_area": 50,
                    "yield_palm_inter": 20,
                    "yield_palm_mono": 22,
                    "yield_crop_inter": 6,
                    "yield_crop_mono": 12,
                },
            )

        self.assertEqual(response.status_code, 200)
        metrics = response.json["data_numerik"]
        benchmarks = metrics["benchmark_biofisika"]
        self.assertEqual(benchmarks["corridor"]["net_corridor_width_m"], 3.79)
        self.assertEqual(benchmarks["hydrology"]["baseline_curve_number"], 82.0)
        self.assertGreater(benchmarks["hydrology"]["runoff_reduction_m3"], 0)
        self.assertEqual(benchmarks["microclimate"]["status"], "SCENARIO_PROJECTION")
        self.assertIn("not Chave", benchmarks["above_ground_biomass"]["methodology_note"])
        self.assertEqual(benchmarks["bio_circularity"]["status"], "SCENARIO_PROJECTION")
        self.assertEqual(benchmarks["bio_circularity"]["pruned_frond_dry_matter_t_ha_year"], 10.8)
        self.assertIn("not measured", benchmarks["bio_circularity"]["methodology_note"])
        self.assertEqual(response.json["metric_statuses"]["biocircularity"], "SCENARIO_PROJECTION")
        valuation = metrics["valuasi_ekonomi_dan_karbon"]
        self.assertEqual(valuation["scenario_carbon_price_usd_per_tco2e"], 15.5)
        self.assertEqual(
            valuation["carbon_value_usd"],
            round(valuation["estimated_carbon_tco2e"] * 15.5, 2),
        )
        self.assertEqual(valuation["status"], "SCENARIO_PROJECTION")
        self.assertIn("Crop revenue is excluded", valuation["methodology_note"])

    def test_system_control_persists_and_validates_scenario_carbon_price(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "settings-test.sqlite")
            connection = sqlite3.connect(db_path)
            connection.execute(
                "CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT, setting_key TEXT, setting_value TEXT)"
            )
            connection.execute(
                "INSERT INTO app_settings (key, value, setting_key, setting_value) VALUES (?, ?, NULL, NULL)",
                ("legacy_config", "preserved"),
            )
            connection.commit()
            connection.close()

            def settings_connection():
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            client = app_module.app.test_client()
            with patch.object(app_module, "get_pure_db_connection", side_effect=settings_connection):
                saved = client.post("/api/settings", json={"carbon_price_usd": "18.75"})
                loaded = client.get("/api/settings")
                invalid = client.post("/api/settings", json={"carbon_price_usd": "-1"})

            self.assertEqual(saved.status_code, 200)
            self.assertEqual(loaded.json["settings"]["carbon_price_usd"], "18.75")
            self.assertEqual(loaded.json["settings"]["legacy_config"], "preserved")
            self.assertEqual(invalid.status_code, 400)

    def test_commit_is_canonical_idempotent_and_reconcilable(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "simulator-test.sqlite")
            database_module.init_db(db_path)
            payload = {
                "kode_kebun": "EST-MDN-010",
                "palm_age_years": 7.5,
                "land_area_ha": 50,
                "crop_name": "Red Ginger",
                "yield_palm_inter_t_ha_period": 20,
                "yield_palm_mono_t_ha_period": 22,
                "yield_crop_inter_t_ha_period": 6,
                "yield_crop_mono_t_ha_period": 12,
            }
            key = "sim-commit-test-key-00000001"

            with patch.object(app_module, "DB_PATH", db_path), patch.object(
                database_module, "DEFAULT_DB_PATH", db_path
            ), patch.object(app_module, "read_local_store", return_value={"simulator_history": []}), patch.object(
                app_module, "save_local_store"
            ), patch.object(app_module, "record_unified_ai_log"):
                client = app_module.app.test_client()
                first = client.post(
                    "/api/simulate",
                    json=payload,
                    headers={"Idempotency-Key": key},
                )
                retry = client.post(
                    "/api/simulate",
                    json=payload,
                    headers={"Idempotency-Key": key},
                )
                changed_payload = dict(payload, land_area_ha=49)
                conflict = client.post(
                    "/api/simulate",
                    json=changed_payload,
                    headers={"Idempotency-Key": key},
                )
                status = client.get(
                    "/api/simulate/commit-status",
                    headers={"Idempotency-Key": key},
                )

            self.assertEqual(first.status_code, 201)
            self.assertEqual(first.json["yield_input_provenance"]["source"], "USER_PROVIDED_UNVERIFIED")
            self.assertFalse(first.json["yield_input_provenance"]["field_measurement_verified"])
            self.assertEqual(retry.status_code, 200)
            self.assertEqual(first.json["ledger"], retry.json["ledger"])
            self.assertEqual(conflict.status_code, 409)
            self.assertEqual(conflict.json["commit_status"], "NOT_COMMITTED")
            self.assertEqual(status.json["commit_status"], "COMMITTED")
            self.assertEqual(status.json["ledger"]["record_id"], first.json["id"])
            self.assertEqual(status.json["snapshot"]["calculation"]["metric_statuses"]["yield_inputs"], "SCENARIO_PROJECTION")

            conn = database_module.get_db_connection(db_path)
            try:
                rows = conn.execute(
                    "SELECT id, sha256_hash, canonical_snapshot_json FROM compute_audit_logs WHERE idempotency_key = ?",
                    (key,),
                ).fetchall()
            finally:
                conn.close()
            self.assertEqual(len(rows), 1)
            snapshot_json = rows[0]["canonical_snapshot_json"]
            self.assertEqual(rows[0]["sha256_hash"], hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest().upper())
            snapshot = json.loads(snapshot_json)
            self.assertEqual(snapshot["record_id"], rows[0]["id"])
            self.assertEqual(snapshot["idempotency_key"], key)
            self.assertEqual(snapshot["ledger_authority"], "LOCAL_SQLITE")

    def test_commit_requires_idempotency_and_complete_yields(self):
        client = app_module.app.test_client()
        no_key = client.post("/api/simulate", json={"kode_kebun": "EST-MDN-010"})
        self.assertEqual(no_key.status_code, 400)
        self.assertEqual(no_key.json["commit_status"], "NOT_COMMITTED")

        missing_yields = client.post(
            "/api/simulate",
            json={"kode_kebun": "EST-MDN-010", "palm_age": 7.5, "land_area": 50},
            headers={"Idempotency-Key": "sim-pending-test-key-0001"},
        )
        self.assertEqual(missing_yields.status_code, 422)
        self.assertEqual(missing_yields.json["commit_status"], "NOT_COMMITTED")
        self.assertEqual(len(missing_yields.json["error"]["fields"]), 4)

    def test_commit_failure_never_returns_a_seal_or_record_id(self):
        payload = {
            "kode_kebun": "EST-MDN-010",
            "palm_age": 7.5,
            "land_area": 50,
            "crop_name": "Red Ginger",
            "yield_palm_inter": 20,
            "yield_palm_mono": 22,
            "yield_crop_inter": 6,
            "yield_crop_mono": 12,
        }
        with patch.object(app_module, "save_simulation_record", side_effect=OSError("ledger unavailable")):
            response = app_module.app.test_client().post(
                "/api/simulate",
                json=payload,
                headers={"Idempotency-Key": "sim-ledger-failure-key-0001"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json["commit_status"], "COMMIT_STATUS_UNKNOWN")
        self.assertNotIn("record_id", response.json)
        self.assertNotIn("sha256_seal", response.json)
        self.assertNotIn("ledger", response.json)

    def test_tbs_pricing_requires_system_control_or_request_inputs(self):
        with patch.object(app_module, "get_all_app_settings", return_value={}):
            response = app_module.app.test_client().get("/api/pricing/tbs-calculation")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "unavailable")
        self.assertEqual(len(response.json["missing_fields"]), 10)
        self.assertNotIn("data", response.json)

        with patch.object(app_module, "get_all_app_settings", return_value={}):
            post_response = app_module.app.test_client().post("/api/pricing/tbs-calculation", json={})
        self.assertEqual(post_response.status_code, 422)
        self.assertEqual(post_response.json["status"], "error")

    def test_tbs_pricing_endpoint_does_not_invent_farm_revenue(self):
        pricing_inputs = {
            "cpo_global": 1500,
            "kurs_usd": 16000,
            "bea_keluar": 100,
            "pe_bpdpks": 80,
            "logistik": 40,
            "p_kernel": 12000,
            "rendemen_cpo": 21,
            "indeks_k": 90,
            "biaya_olah": 250,
            "rendemen_kernel": 5,
        }

        with patch.object(app_module, "get_all_app_settings", return_value={}):
            response = app_module.app.test_client().post(
                "/api/pricing/tbs-calculation",
                json=pricing_inputs,
            )

        expected_tbs_per_ton, _, expected_tbs_per_kg = app_module.hitung_harga_tbs_per_ton(
            p_int_usd_mt=1500,
            kurs_usd_idr=16000,
            bk_usd_mt=100,
            pe_usd_mt=80,
            logistik_usd_mt=40,
            p_kernel_idr_kg=12000,
            rendemen_cpo=0.21,
            indeks_k=0.9,
            biaya_olah_idr_kg=250,
            rendemen_kernel=0.05,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["pricing_status"]["mode"], "SCENARIO_ONLY")
        self.assertFalse(response.json["pricing_status"]["inputs_independently_verified"])
        self.assertFalse(response.json["pricing_status"]["live_market_feed_connected"])
        self.assertEqual(response.json["data"]["harga_tbs_idr_kg"], round(expected_tbs_per_kg, 2))
        self.assertEqual(response.json["data"]["harga_tbs_idr_ton"], round(expected_tbs_per_ton, 2))
        self.assertIsNone(response.json["financial_real"])
        self.assertIsNone(response.json["comprehensive_financials"])

    def test_legacy_simulation_endpoint_rejects_missing_yields(self):
        response = app_module.app.test_client().post(
            "/api/simulate/run",
            json={"kode_kebun": "EST-MDN-010", "land_area": 640},
        )

        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.json["success"])
        self.assertEqual(len(response.json["missing_fields"]), 4)


if __name__ == "__main__":
    unittest.main()
