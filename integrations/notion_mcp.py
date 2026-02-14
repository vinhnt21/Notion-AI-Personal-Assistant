"""Wrapper for Notion API operations with auto-discovery."""

from typing import List, Dict, Any, Optional
from notion_client import Client
from config import config
from integrations.notion_discovery import NotionWorkspaceDiscovery, DatabaseInfo


class NotionMCP:
    """Unified wrapper around the Notion API with workspace auto-discovery"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
    ):
        self.api_key = api_key or config.get_api_key("notion")
        if not self.api_key:
            raise ValueError("Notion API key required — set NOTION_API_KEY in .env")

        self.client = Client(auth=self.api_key)

        # Workspace discovery
        self.discovery = NotionWorkspaceDiscovery(
            client=self.client,
            parent_page_id=parent_page_id or config.notion_parent_page_id,
        )

        # Load from cache or discover fresh
        if not self.discovery.load_cache():
            print("[NotionMCP] Discovering databases in workspace…")
            self.discovery.discover_all_databases()

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def refresh_databases(self) -> Dict[str, DatabaseInfo]:
        """Force-refresh the database list"""
        return self.discovery.discover_all_databases()

    def get_database_id(self, database_name: str) -> Optional[str]:
        """Resolve a human-readable database name to its Notion ID"""
        db_info = self.discovery.get_database_by_name(database_name)
        return db_info.id if db_info else None

    def list_available_databases(self) -> List[str]:
        """List all discovered database names"""
        return self.discovery.list_all_databases()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self, query: str, filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the Notion workspace.

        Args:
            query: Search query string
            filter_type: Optional — 'page' or 'database'
        """
        params: Dict[str, Any] = {"query": query}
        if filter_type:
            # Notion API uses "data_source" instead of "database"
            value = "data_source" if filter_type == "database" else filter_type
            params["filter"] = {"property": "object", "value": value}

        response = self.client.search(**params)
        return response.get("results", [])

    # ------------------------------------------------------------------
    # Database operations
    # ------------------------------------------------------------------

    def query_database(
        self,
        database_id: str,
        filter_params: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Query a database by its ID (uses data_sources endpoint in SDK v2.7+)"""
        params: Dict[str, Any] = {}
        if filter_params:
            params["filter"] = filter_params
        if sorts:
            params["sorts"] = sorts

        response = self.client.data_sources.query(
            data_source_id=database_id, **params
        )
        return response.get("results", [])

    def query_database_by_name(
        self,
        database_name: str,
        filter_params: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Query a database by its human-readable name"""
        db_id = self.get_database_id(database_name)
        if not db_id:
            raise ValueError(f"Database '{database_name}' not found")
        return self.query_database(db_id, filter_params, sorts)

    def create_database_entry(
        self, database_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new row in a database"""
        return self.client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
        )

    def update_database_entry(
        self, page_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing database row"""
        return self.client.pages.update(page_id=page_id, properties=properties)

    # ------------------------------------------------------------------
    # Page operations
    # ------------------------------------------------------------------

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page by ID"""
        return self.client.pages.retrieve(page_id=page_id)

    def create_page(
        self,
        parent_id: str,
        title: str,
        properties: Optional[Dict] = None,
        children: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Create a new page under a parent page"""
        page_data: Dict[str, Any] = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": {"title": [{"text": {"content": title}}]}
            },
        }

        if properties:
            page_data["properties"].update(properties)
        if children:
            page_data["children"] = children

        return self.client.pages.create(**page_data)

    def update_page(
        self, page_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update page properties"""
        return self.client.pages.update(page_id=page_id, properties=properties)

    # ------------------------------------------------------------------
    # Block operations
    # ------------------------------------------------------------------

    def get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """Get children blocks of a page / block"""
        response = self.client.blocks.children.list(block_id=block_id)
        return response.get("results", [])

    def append_block_children(
        self, block_id: str, children: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Append new blocks to a page / block"""
        return self.client.blocks.children.append(
            block_id=block_id, children=children
        )
