"""
Persistent storage layer for Marcos memory using SQLite.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from .schema import System, PressurePoint, PatternSynthesis
from ..config import MEMORY_DB_PATH


class MemoryStorage:
    """Persistent storage for Marcos's accumulated memories."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or MEMORY_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Systems table - stores analyzed systems
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS systems (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    domain TEXT NOT NULL,
                    pressure_points_json TEXT,
                    connections_json TEXT,
                    human_pattern_observed TEXT,
                    prediction TEXT,
                    raw_input TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Connections table - for cross-referencing related systems
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_system_id TEXT NOT NULL,
                    target_system_id TEXT NOT NULL,
                    connection_type TEXT,
                    strength REAL DEFAULT 0.5,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_system_id) REFERENCES systems(id),
                    FOREIGN KEY (target_system_id) REFERENCES systems(id),
                    UNIQUE(source_system_id, target_system_id)
                )
            """)

            # Pattern syntheses table - stores meta-patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pattern_syntheses (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    description TEXT,
                    supporting_systems_json TEXT,
                    domains_involved_json TEXT,
                    frequency INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 0.5,
                    insights_json TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Domains table - for quick domain lookups
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    system_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Full-text search for systems
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS systems_fts USING fts5(
                    name, description, domain, human_pattern_observed, prediction,
                    content='systems',
                    content_rowid='rowid'
                )
            """)

            # Indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_domain ON systems(domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_timestamp ON systems(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern_type ON pattern_syntheses(pattern_type)")

    def save_system(self, system: System) -> str:
        """Save a system to memory. Returns the system ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO systems
                (id, name, description, domain, pressure_points_json, connections_json,
                 human_pattern_observed, prediction, raw_input, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                system.id,
                system.name,
                system.description,
                system.domain,
                json.dumps([pp.to_dict() for pp in system.pressure_points]),
                json.dumps(system.connections),
                system.human_pattern_observed,
                system.prediction,
                system.raw_input,
                system.timestamp.isoformat(),
            ))

            # Update FTS index
            cursor.execute("""
                INSERT OR REPLACE INTO systems_fts (rowid, name, description, domain,
                    human_pattern_observed, prediction)
                SELECT rowid, name, description, domain, human_pattern_observed, prediction
                FROM systems WHERE id = ?
            """, (system.id,))

            # Update domain count
            cursor.execute("""
                INSERT INTO domains (name, system_count) VALUES (?, 1)
                ON CONFLICT(name) DO UPDATE SET system_count = system_count + 1
            """, (system.domain,))

            # Save connections
            for target_id in system.connections:
                self._save_connection(cursor, system.id, target_id)

        return system.id

    def _save_connection(self, cursor, source_id: str, target_id: str,
                         connection_type: str = "related", strength: float = 0.5,
                         reason: str = ""):
        """Save a connection between two systems."""
        cursor.execute("""
            INSERT OR IGNORE INTO system_connections
            (source_system_id, target_system_id, connection_type, strength, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (source_id, target_id, connection_type, strength, reason))

    def get_system(self, system_id: str) -> Optional[System]:
        """Retrieve a system by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM systems WHERE id = ?", (system_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_system(row)
            return None

    def _row_to_system(self, row: sqlite3.Row) -> System:
        """Convert a database row to a System object."""
        pressure_points = [
            PressurePoint.from_dict(pp)
            for pp in json.loads(row["pressure_points_json"] or "[]")
        ]
        connections = json.loads(row["connections_json"] or "[]")

        return System(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            domain=row["domain"],
            pressure_points=pressure_points,
            connections=connections,
            human_pattern_observed=row["human_pattern_observed"] or "",
            prediction=row["prediction"] or "",
            raw_input=row["raw_input"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    def get_all_systems(self, limit: int = 100, offset: int = 0) -> list[System]:
        """Retrieve all systems, ordered by timestamp descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM systems
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            return [self._row_to_system(row) for row in cursor.fetchall()]

    def get_systems_by_domain(self, domain: str) -> list[System]:
        """Retrieve all systems in a specific domain."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM systems WHERE domain = ? ORDER BY timestamp DESC
            """, (domain,))

            return [self._row_to_system(row) for row in cursor.fetchall()]

    def get_connected_systems(self, system_id: str) -> list[tuple[System, float]]:
        """Get systems connected to a given system with their connection strength."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, sc.strength
                FROM systems s
                JOIN system_connections sc ON s.id = sc.target_system_id
                WHERE sc.source_system_id = ?
                UNION
                SELECT s.*, sc.strength
                FROM systems s
                JOIN system_connections sc ON s.id = sc.source_system_id
                WHERE sc.target_system_id = ?
            """, (system_id, system_id))

            results = []
            for row in cursor.fetchall():
                system = self._row_to_system(row)
                strength = row["strength"]
                results.append((system, strength))
            return results

    def add_connection(self, source_id: str, target_id: str,
                       connection_type: str = "related",
                       strength: float = 0.5, reason: str = ""):
        """Add a connection between two systems."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            self._save_connection(cursor, source_id, target_id,
                                  connection_type, strength, reason)

    def save_synthesis(self, synthesis: PatternSynthesis) -> str:
        """Save a pattern synthesis to memory."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO pattern_syntheses
                (id, title, pattern_type, description, supporting_systems_json,
                 domains_involved_json, frequency, confidence, insights_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                synthesis.id,
                synthesis.title,
                synthesis.pattern_type,
                synthesis.description,
                json.dumps(synthesis.supporting_systems),
                json.dumps(synthesis.domains_involved),
                synthesis.frequency,
                synthesis.confidence,
                json.dumps(synthesis.insights),
                synthesis.timestamp.isoformat(),
            ))

        return synthesis.id

    def get_all_syntheses(self, pattern_type: Optional[str] = None) -> list[PatternSynthesis]:
        """Retrieve all pattern syntheses, optionally filtered by type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if pattern_type:
                cursor.execute("""
                    SELECT * FROM pattern_syntheses
                    WHERE pattern_type = ?
                    ORDER BY confidence DESC, frequency DESC
                """, (pattern_type,))
            else:
                cursor.execute("""
                    SELECT * FROM pattern_syntheses
                    ORDER BY confidence DESC, frequency DESC
                """)

            return [self._row_to_synthesis(row) for row in cursor.fetchall()]

    def _row_to_synthesis(self, row: sqlite3.Row) -> PatternSynthesis:
        """Convert a database row to a PatternSynthesis object."""
        return PatternSynthesis(
            id=row["id"],
            title=row["title"],
            pattern_type=row["pattern_type"],
            description=row["description"] or "",
            supporting_systems=json.loads(row["supporting_systems_json"] or "[]"),
            domains_involved=json.loads(row["domains_involved_json"] or "[]"),
            frequency=row["frequency"],
            confidence=row["confidence"],
            insights=json.loads(row["insights_json"] or "[]"),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    def get_domains(self) -> list[tuple[str, int]]:
        """Get all domains with their system counts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, system_count FROM domains
                ORDER BY system_count DESC
            """)
            return [(row["name"], row["system_count"]) for row in cursor.fetchall()]

    def get_system_count(self) -> int:
        """Get total number of systems in memory."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM systems")
            return cursor.fetchone()["count"]

    def get_synthesis_count(self) -> int:
        """Get total number of pattern syntheses."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM pattern_syntheses")
            return cursor.fetchone()["count"]

    def delete_system(self, system_id: str) -> bool:
        """Delete a system from memory."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM systems WHERE id = ?", (system_id,))
            cursor.execute("""
                DELETE FROM system_connections
                WHERE source_system_id = ? OR target_system_id = ?
            """, (system_id, system_id))
            return cursor.rowcount > 0
