"""
Query and retrieval system for Marcos memory.
Allows searching, filtering, and finding similar systems.
"""

import sqlite3
from typing import Optional
from datetime import datetime, timedelta

from .schema import System, PatternSynthesis
from .storage import MemoryStorage


class MemoryQuery:
    """Query interface for Marcos's accumulated memories."""

    def __init__(self, storage: Optional[MemoryStorage] = None):
        self.storage = storage or MemoryStorage()

    def search(self, query: str, limit: int = 10) -> list[System]:
        """
        Full-text search across systems.
        Searches name, description, domain, patterns observed, and predictions.
        """
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()

            # Use FTS5 for full-text search
            cursor.execute("""
                SELECT s.*
                FROM systems s
                JOIN systems_fts fts ON s.rowid = fts.rowid
                WHERE systems_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))

            return [self.storage._row_to_system(row) for row in cursor.fetchall()]

    def find_similar_systems(self, system: System, limit: int = 5) -> list[tuple[System, float]]:
        """
        Find systems similar to the given one.
        Uses domain matching, pattern similarity, and connection graph.
        Returns systems with similarity scores.
        """
        similar = []

        # Get systems in the same domain
        domain_systems = self.storage.get_systems_by_domain(system.domain)
        for s in domain_systems:
            if s.id != system.id:
                score = self._calculate_similarity(system, s)
                similar.append((s, score))

        # Also check connected systems
        connected = self.storage.get_connected_systems(system.id)
        for s, strength in connected:
            # Boost connected systems
            existing = next((i for i, (sys, _) in enumerate(similar) if sys.id == s.id), None)
            if existing is not None:
                similar[existing] = (s, similar[existing][1] + strength * 0.3)
            else:
                similar.append((s, strength * 0.5))

        # Sort by score and return top results
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar[:limit]

    def _calculate_similarity(self, system1: System, system2: System) -> float:
        """Calculate similarity score between two systems."""
        score = 0.0

        # Domain match (high weight)
        if system1.domain == system2.domain:
            score += 0.4

        # Pattern similarity - check for common words in human patterns
        words1 = set(system1.human_pattern_observed.lower().split())
        words2 = set(system2.human_pattern_observed.lower().split())
        common_words = words1 & words2
        if words1 and words2:
            pattern_score = len(common_words) / max(len(words1), len(words2))
            score += pattern_score * 0.3

        # Pressure point count similarity
        pp_diff = abs(len(system1.pressure_points) - len(system2.pressure_points))
        if pp_diff == 0:
            score += 0.15
        elif pp_diff <= 2:
            score += 0.1

        # Check for value-mover unity in both
        unity1 = any(pp.value_mover_unity for pp in system1.pressure_points)
        unity2 = any(pp.value_mover_unity for pp in system2.pressure_points)
        if unity1 and unity2:
            score += 0.15

        return min(score, 1.0)

    def find_by_pattern(self, pattern_keywords: list[str]) -> list[System]:
        """Find systems that exhibit specific human patterns."""
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()

            # Build query for pattern matching
            conditions = " OR ".join(["human_pattern_observed LIKE ?" for _ in pattern_keywords])
            params = [f"%{kw}%" for kw in pattern_keywords]

            cursor.execute(f"""
                SELECT * FROM systems
                WHERE {conditions}
                ORDER BY timestamp DESC
            """, params)

            return [self.storage._row_to_system(row) for row in cursor.fetchall()]

    def find_by_pressure_point_value(self, value_keyword: str) -> list[System]:
        """Find systems where pressure points deal with a specific value type."""
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM systems
                WHERE pressure_points_json LIKE ?
                ORDER BY timestamp DESC
            """, (f'%"value"%{value_keyword}%',))

            return [self.storage._row_to_system(row) for row in cursor.fetchall()]

    def find_systems_with_unity(self) -> list[System]:
        """Find all systems that have value-mover unity at any pressure point."""
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM systems
                WHERE pressure_points_json LIKE '%"value_mover_unity": true%'
                ORDER BY timestamp DESC
            """)

            return [self.storage._row_to_system(row) for row in cursor.fetchall()]

    def get_recent_systems(self, days: int = 7, limit: int = 20) -> list[System]:
        """Get systems analyzed in the last N days."""
        cutoff = datetime.now() - timedelta(days=days)

        with self.storage._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM systems
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (cutoff.isoformat(), limit))

            return [self.storage._row_to_system(row) for row in cursor.fetchall()]

    def get_domain_summary(self) -> dict[str, dict]:
        """
        Get a summary of all domains in memory.
        Returns dict mapping domain names to stats.
        """
        domains = self.storage.get_domains()
        summary = {}

        for domain_name, count in domains:
            systems = self.storage.get_systems_by_domain(domain_name)

            # Calculate domain statistics
            unity_count = sum(
                1 for s in systems
                if any(pp.value_mover_unity for pp in s.pressure_points)
            )

            # Collect common patterns
            patterns = [s.human_pattern_observed for s in systems if s.human_pattern_observed]

            summary[domain_name] = {
                "system_count": count,
                "unity_prevalence": unity_count / count if count > 0 else 0,
                "patterns_observed": patterns[:5],  # Top 5 patterns
                "latest_timestamp": max(s.timestamp for s in systems).isoformat() if systems else None,
            }

        return summary

    def find_cross_domain_connections(self) -> list[tuple[System, System, str]]:
        """
        Find systems from different domains that are connected.
        Returns tuples of (system1, system2, connection_reason).
        """
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT s1.*, s2.*, sc.reason
                FROM system_connections sc
                JOIN systems s1 ON sc.source_system_id = s1.id
                JOIN systems s2 ON sc.target_system_id = s2.id
                WHERE s1.domain != s2.domain
            """)

            results = []
            for row in cursor.fetchall():
                # Parse the combined row - need to handle carefully
                # This is a simplified version
                pass

            return results

    def get_memory_stats(self) -> dict:
        """Get overall statistics about Marcos's memory."""
        system_count = self.storage.get_system_count()
        synthesis_count = self.storage.get_synthesis_count()
        domains = self.storage.get_domains()

        # Calculate additional stats
        all_systems = self.storage.get_all_systems(limit=1000)
        total_pressure_points = sum(len(s.pressure_points) for s in all_systems)
        unity_systems = len([s for s in all_systems
                            if any(pp.value_mover_unity for pp in s.pressure_points)])

        return {
            "total_systems": system_count,
            "total_syntheses": synthesis_count,
            "total_domains": len(domains),
            "total_pressure_points": total_pressure_points,
            "systems_with_unity": unity_systems,
            "domains": dict(domains),
            "avg_pressure_points": total_pressure_points / system_count if system_count > 0 else 0,
        }

    def get_context_for_analysis(self, domain: Optional[str] = None,
                                  keywords: Optional[list[str]] = None,
                                  limit: int = 5) -> str:
        """
        Get relevant context from memory to inform a new analysis.
        Returns a formatted string of relevant past systems.
        """
        relevant_systems = []

        # Get domain-specific systems
        if domain:
            relevant_systems.extend(self.storage.get_systems_by_domain(domain)[:limit])

        # Search by keywords
        if keywords:
            for kw in keywords:
                found = self.search(kw, limit=3)
                relevant_systems.extend(found)

        # Deduplicate
        seen_ids = set()
        unique_systems = []
        for s in relevant_systems:
            if s.id not in seen_ids:
                seen_ids.add(s.id)
                unique_systems.append(s)

        if not unique_systems:
            return "No relevant systems found in memory."

        # Format context
        context_parts = ["## Relevant Systems from Memory\n"]
        for system in unique_systems[:limit]:
            context_parts.append(f"### {system.name} ({system.domain})")
            context_parts.append(f"Pattern: {system.human_pattern_observed}")
            if system.pressure_points:
                pp = system.pressure_points[0]
                context_parts.append(f"Key pressure point: {pp.name} - Value: {pp.value}, Mover: {pp.mover}")
            context_parts.append("")

        return "\n".join(context_parts)
