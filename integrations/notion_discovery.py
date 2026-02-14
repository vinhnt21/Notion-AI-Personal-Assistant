"""Auto-discover and cache all databases in a Notion workspace."""

from typing import Dict, List, Optional, Any
from notion_client import Client
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class DatabaseInfo:
    """Information about a discovered Notion database"""

    id: str
    title: str
    properties: Dict[str, Any]
    parent_page_id: str


class NotionWorkspaceDiscovery:
    """Automatically discover and manage databases in a Notion workspace"""

    def __init__(self, client: Client, parent_page_id: Optional[str] = None):
        self.client = client
        self.parent_page_id = parent_page_id
        self._databases_cache: Dict[str, DatabaseInfo] = {}
        self.cache_file = Path("data/databases_cache.json")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover_all_databases(self) -> Dict[str, DatabaseInfo]:
        """
        Discover all databases in the workspace.

        Returns:
            Dict mapping database_title -> DatabaseInfo
        """
        databases: Dict[str, DatabaseInfo] = {}

        # Method 1: If a parent page is configured, scan its children recursively
        if self.parent_page_id:
            databases.update(self._get_child_databases(self.parent_page_id))

        # Method 2: Search the entire workspace for databases
        search_results = self._search_all_databases()
        databases.update(search_results)

        # Persist
        self._databases_cache = databases
        self._save_cache()

        return databases

    def get_database_by_name(self, name: str) -> Optional[DatabaseInfo]:
        """Find a database by name with fuzzy matching"""
        # Exact match
        if name in self._databases_cache:
            return self._databases_cache[name]

        # Case-insensitive match
        for db_name, db_info in self._databases_cache.items():
            if db_name.lower() == name.lower():
                return db_info

        # Partial / substring match
        for db_name, db_info in self._databases_cache.items():
            if name.lower() in db_name.lower():
                return db_info

        return None

    def list_all_databases(self) -> List[str]:
        """Return names of all cached databases"""
        return list(self._databases_cache.keys())

    def get_database_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the property schema of a database by name"""
        db = self.get_database_by_name(name)
        if db:
            return db.properties
        return None

    # ------------------------------------------------------------------
    # Cache I/O
    # ------------------------------------------------------------------

    def load_cache(self) -> bool:
        """Load database cache from disk. Returns True on success."""
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            self._databases_cache = {
                name: DatabaseInfo(**data) for name, data in cache_data.items()
            }
            return True
        except Exception:
            return False

    def _save_cache(self):
        """Persist the database cache to disk"""
        cache_data = {
            name: asdict(db) for name, db in self._databases_cache.items()
        }

        self.cache_file.parent.mkdir(exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Internal discovery helpers
    # ------------------------------------------------------------------

    def _get_child_databases(self, page_id: str) -> Dict[str, DatabaseInfo]:
        """Recursively scan child blocks of a page for databases"""
        databases: Dict[str, DatabaseInfo] = {}

        try:
            has_more = True
            start_cursor = None

            while has_more:
                params: Dict[str, Any] = {
                    "block_id": page_id,
                    "page_size": 100,
                }
                if start_cursor:
                    params["start_cursor"] = start_cursor

                blocks = self.client.blocks.children.list(**params)

                for block in blocks.get("results", []):
                    block_type = block.get("type")

                    if block_type == "child_database":
                        db_id = block["id"]
                        db_info = self.client.databases.retrieve(database_id=db_id)
                        title = self._extract_database_title(db_info)

                        databases[title] = DatabaseInfo(
                            id=db_id,
                            title=title,
                            properties=db_info.get("properties", {}),
                            parent_page_id=page_id,
                        )

                    elif block_type == "child_page":
                        # Recurse into child pages
                        child_dbs = self._get_child_databases(block["id"])
                        databases.update(child_dbs)

                has_more = blocks.get("has_more", False)
                start_cursor = blocks.get("next_cursor")

        except Exception as e:
            print(f"[NotionDiscovery] Error scanning page {page_id}: {e}")

        return databases

    def _search_all_databases(self) -> Dict[str, DatabaseInfo]:
        """Search the entire workspace for databases"""
        databases: Dict[str, DatabaseInfo] = {}

        try:
            has_more = True
            start_cursor = None

            while has_more:
                params: Dict[str, Any] = {
                    "filter": {"property": "object", "value": "data_source"},
                }
                if start_cursor:
                    params["start_cursor"] = start_cursor

                results = self.client.search(**params)

                for db in results.get("results", []):
                    db_id = db["id"]
                    title = self._extract_database_title(db)

                    databases[title] = DatabaseInfo(
                        id=db_id,
                        title=title,
                        properties=db.get("properties", {}),
                        parent_page_id=db.get("parent", {}).get("page_id", ""),
                    )

                has_more = results.get("has_more", False)
                start_cursor = results.get("next_cursor")

        except Exception as e:
            print(f"[NotionDiscovery] Error searching databases: {e}")

        return databases

    @staticmethod
    def _extract_database_title(database: Dict[str, Any]) -> str:
        """Extract the plain-text title from a database object"""
        title_prop = database.get("title", [])
        if title_prop and len(title_prop) > 0:
            return title_prop[0].get("plain_text", "Untitled")
        return "Untitled"
