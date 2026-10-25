import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import get_db_connection, init_db


class TestInspectionEvidenceSchemaMigration(unittest.TestCase):
    def test_new_database_declares_process_stage_and_accepts_workflow_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "new.db"

            with (
                patch("database.seed_canonical_estates"),
                patch("database.seed_roadmap_milestones"),
                patch("database.seed_canonical_inspection_evidence"),
            ):
                init_db(str(db_path))

            connection = sqlite3.connect(db_path)
            try:
                columns = {
                    row[1] for row in connection.execute(
                        "PRAGMA table_info(inspection_evidence)"
                    )
                }
                self.assertIn("process_stage", columns)
                self.assertIn("camera_pitch_degrees", columns)
                process_stage_default = next(
                    row[4] for row in connection.execute(
                        "PRAGMA table_info(inspection_evidence)"
                    )
                    if row[1] == "process_stage"
                )
                self.assertEqual(process_stage_default, "'STAGE_3'")

                connection.execute("""
                    INSERT INTO inspection_evidence (
                        id, image_base64, sha256_hash, process_stage
                    ) VALUES (?, ?, ?, ?)
                """, ("new-evidence", "image-data", "new-hash", "STAGE-0-ANNUAL-REG"))
                connection.commit()
            finally:
                connection.close()

    def test_adds_process_stage_to_existing_inspection_evidence_table(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "legacy.db"
            connection = sqlite3.connect(db_path)
            connection.execute("""
                CREATE TABLE inspection_evidence (
                    id TEXT PRIMARY KEY,
                    dossier_id TEXT NOT NULL DEFAULT 'EST-MDN-001',
                    block_id TEXT NOT NULL DEFAULT 'Blok A',
                    perspective_mode TEXT NOT NULL DEFAULT 'TERRESTRIAL_IN_SITU',
                    altitude_agl_m REAL DEFAULT 1.45,
                    camera_pitch_deg REAL DEFAULT -12.0,
                    latitude REAL DEFAULT 0.824100,
                    longitude REAL DEFAULT 99.561200,
                    image_mime_type TEXT NOT NULL DEFAULT 'image/jpeg',
                    image_base64 TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    detected_entities_json TEXT,
                    diagnostic_matrix_json TEXT,
                    synced_to_bigquery INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            connection.execute(
                "INSERT INTO inspection_evidence (id, image_base64, sha256_hash) VALUES (?, ?, ?)",
                ("legacy-evidence", "image-data", "legacy-hash"),
            )
            connection.commit()
            connection.close()

            with (
                patch("database.seed_canonical_estates"),
                patch("database.seed_roadmap_milestones"),
                patch("database.seed_canonical_inspection_evidence"),
            ):
                init_db(str(db_path))

            connection = sqlite3.connect(db_path)
            try:
                columns = {
                    row[1] for row in connection.execute(
                        "PRAGMA table_info(inspection_evidence)"
                    )
                }
                self.assertIn("process_stage", columns)
                self.assertIn("camera_pitch_degrees", columns)
                stage = connection.execute(
                    "SELECT process_stage FROM inspection_evidence WHERE id = ?",
                    ("legacy-evidence",),
                ).fetchone()[0]
                self.assertEqual(stage, "STAGE_3")

                connection.execute("""
                    INSERT INTO inspection_evidence (
                        id, image_base64, sha256_hash, process_stage, camera_pitch_degrees
                    ) VALUES (?, ?, ?, ?, ?)
                """, ("new-evidence", "image-data", "new-hash", "STAGE-2-Q2", -12.0))
                connection.commit()
            finally:
                connection.close()

    def test_connection_migrates_legacy_schema_before_writers_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "connection-migration.db"
            connection = sqlite3.connect(db_path)
            connection.execute("""
                CREATE TABLE inspection_evidence (
                    id TEXT PRIMARY KEY,
                    image_base64 TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL
                )
            """)
            connection.commit()
            connection.close()

            with patch("database.DEFAULT_DB_PATH", str(db_path)):
                connection = get_db_connection()
                try:
                    columns = {
                        row[1] for row in connection.execute(
                            "PRAGMA table_info(inspection_evidence)"
                        )
                    }
                    self.assertIn("process_stage", columns)
                    default = next(
                        row[4] for row in connection.execute(
                            "PRAGMA table_info(inspection_evidence)"
                        )
                        if row[1] == "process_stage"
                    )
                    self.assertEqual(default, "'STAGE_3'")
                finally:
                    connection.close()

    def test_schema_engine_connection_migrates_legacy_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "schema-engine-legacy.db"
            connection = sqlite3.connect(db_path)
            connection.execute("""
                CREATE TABLE inspection_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    dossier_id TEXT NOT NULL
                )
            """)
            connection.commit()
            connection.close()

            with patch("database_schema_engine.DB_PATH", str(db_path)):
                from database_schema_engine import get_db_connection

                connection = get_db_connection()
                try:
                    columns = {
                        row[1] for row in connection.execute(
                            "PRAGMA table_info(inspection_evidence)"
                        )
                    }
                    self.assertIn("process_stage", columns)
                    default = next(
                        row[4] for row in connection.execute(
                            "PRAGMA table_info(inspection_evidence)"
                        )
                        if row[1] == "process_stage"
                    )
                    self.assertEqual(default, "'STAGE_3'")
                finally:
                    connection.close()

    def test_new_schema_engine_table_accepts_default_stage_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "schema-engine-new.db"
            with patch("database_schema_engine.DB_PATH", str(db_path)):
                from database_schema_engine import initialize_pure_relational_schema

                initialize_pure_relational_schema()

            connection = sqlite3.connect(db_path)
            try:
                connection.execute("PRAGMA foreign_keys = OFF")
                connection.execute("""
                    INSERT INTO inspection_evidence (
                        evidence_id, dossier_id, mandor_id, audit_year, quarter_cycle,
                        perspective_mode, altitude_agl_m, camera_pitch_degrees,
                        latitude_exif, longitude_exif, image_raw_base64,
                        image_sha256_hash, file_size_bytes, detected_entities_json,
                        root_clearance_verified_m, weather_satellite_validation
                    ) VALUES (
                        'EV-DEFAULT-STAGE', 'EST-TEST', 'MDR-TEST', 2026, 'Q1',
                        'AERIAL_DRONE', 45, -90, 0.8241, 99.5612, 'image-data',
                        'hash-default-stage', 10, '[]', 2.05, 'NOT_CHECKED'
                    )
                """)
                stage = connection.execute(
                    "SELECT process_stage FROM inspection_evidence WHERE evidence_id = ?",
                    ("EV-DEFAULT-STAGE",),
                ).fetchone()[0]
                self.assertEqual(stage, "STAGE_3")
            finally:
                connection.close()

    def test_schema_engine_creates_and_migrates_field_surveillance_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "surveillance-schema.db"
            connection = sqlite3.connect(db_path)
            connection.execute("""
                CREATE TABLE field_surveillance_records (
                    id_log TEXT PRIMARY KEY,
                    kode_kebun TEXT,
                    sha256_seal TEXT
                )
            """)
            connection.execute(
                "INSERT INTO field_surveillance_records (id_log, kode_kebun) VALUES (?, ?)",
                ("legacy-log-1", "EST-LEGACY-001"),
            )
            connection.commit()
            connection.close()

            with patch("database_schema_engine.DB_PATH", str(db_path)):
                from database_schema_engine import initialize_pure_relational_schema

                initialize_pure_relational_schema()

            connection = sqlite3.connect(db_path)
            try:
                columns = {
                    row[1] for row in connection.execute(
                        "PRAGMA table_info(field_surveillance_records)"
                    )
                }
                self.assertTrue({
                    "record_id",
                    "dossier_id",
                    "estate_id",
                    "process_stage",
                    "periode_siklus",
                    "evidence_id",
                    "foto_url",
                    "detected_entities_json",
                    "recorded_at",
                }.issubset(columns))
                migrated = connection.execute("""
                    SELECT record_id, dossier_id, recorded_at
                    FROM field_surveillance_records
                    WHERE id_log = ?
                """, ("legacy-log-1",)).fetchone()
                self.assertEqual(migrated[0], "legacy-log-1")
                self.assertEqual(migrated[1], "EST-LEGACY-001")
                self.assertIsNotNone(migrated[2])
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
