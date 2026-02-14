"""LangChain tool wrappers for Notion operations."""

import json
from typing import List, Optional
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field
from integrations.notion_mcp import NotionMCP
from integrations.notion_schemas import extract_property_value


# ── Tool input schemas ────────────────────────────────────────────────

class SearchNotionInput(BaseModel):
    query: str = Field(description="Search query string")
    filter_type: Optional[str] = Field(
        default=None, description="Filter by 'page' or 'database'"
    )


class QueryDatabaseByNameInput(BaseModel):
    database_name: str = Field(
        description="Name of the database, e.g. 'Tasks', 'Projects'"
    )


class CreatePageInput(BaseModel):
    parent_id: str = Field(description="Parent page ID")
    title: str = Field(description="Page title")
    content: Optional[str] = Field(default=None, description="Page body text")


class CreateDatabaseEntryInput(BaseModel):
    database_name: str = Field(description="Database name")
    properties_json: str = Field(
        description="JSON string of Notion properties to set"
    )


class GetDatabaseSchemaInput(BaseModel):
    database_name: str = Field(description="Database name to inspect")


# ── Tool factory ──────────────────────────────────────────────────────

class NotionToolFactory:
    """Creates LangChain tools that operate on a Notion workspace"""

    def __init__(self, notion_mcp: NotionMCP):
        self.notion = notion_mcp

    def create_tools(self) -> List:
        """Return the full set of Notion tools for the agent"""
        return [
            self._create_list_databases_tool(),
            self._create_get_database_schema_tool(),
            self._create_search_tool(),
            self._create_query_database_tool(),
            self._create_create_page_tool(),
            self._create_create_entry_tool(),
        ]

    # ── individual tool builders ──────────────────────────────────────

    def _create_list_databases_tool(self) -> Tool:
        def list_databases(_input: str = "") -> str:
            databases = self.notion.list_available_databases()
            if not databases:
                return "No databases found. Try refreshing with the refresh command."
            output = "Available databases:\n"
            for idx, db_name in enumerate(databases, 1):
                output += f"{idx}. {db_name}\n"
            return output

        return Tool(
            name="list_databases",
            func=list_databases,
            description=(
                "List all available databases in the Notion workspace. "
                "Use this first to discover what databases exist."
            ),
        )

    def _create_get_database_schema_tool(self) -> StructuredTool:
        def get_schema(database_name: str) -> str:
            schema = self.notion.discovery.get_database_schema(database_name)
            if not schema:
                return f"Database '{database_name}' not found."
            output = f"Schema for '{database_name}':\n"
            for prop_name, prop_info in schema.items():
                prop_type = prop_info.get("type", "unknown")
                output += f"  - {prop_name} ({prop_type})\n"
            return output

        return StructuredTool.from_function(
            func=get_schema,
            name="get_database_schema",
            description=(
                "Get the property schema (column names and types) of a database. "
                "Use this to understand what fields a database has before querying or creating entries."
            ),
            args_schema=GetDatabaseSchemaInput,
        )

    def _create_search_tool(self) -> StructuredTool:
        def search_notion(
            query: str, filter_type: Optional[str] = None
        ) -> str:
            results = self.notion.search(query, filter_type)
            if not results:
                return f"No results found for '{query}'"

            output = f"Found {len(results)} results for '{query}':\n"
            for idx, result in enumerate(results[:10], 1):
                title = "Untitled"
                if "properties" in result:
                    for _, prop in result["properties"].items():
                        if prop.get("type") == "title":
                            title_arr = prop.get("title", [])
                            if title_arr:
                                title = title_arr[0].get("plain_text", "Untitled")
                            break

                obj_type = result.get("object", "unknown")
                output += f"{idx}. [{obj_type}] {title} (ID: {result['id']})\n"
            return output

        return StructuredTool.from_function(
            func=search_notion,
            name="search_notion",
            description=(
                "Search for pages and databases in the Notion workspace by keywords."
            ),
            args_schema=SearchNotionInput,
        )

    def _create_query_database_tool(self) -> StructuredTool:
        def query_database_by_name(database_name: str) -> str:
            try:
                results = self.notion.query_database_by_name(database_name)
            except ValueError as e:
                return str(e)

            if not results:
                return f"No entries found in '{database_name}'"

            output = f"Found {len(results)} entries in '{database_name}':\n"
            for idx, entry in enumerate(results[:15], 1):
                properties = entry.get("properties", {})

                # Find the title column
                entry_title = "No title"
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        title_arr = prop_value.get("title", [])
                        if title_arr:
                            entry_title = title_arr[0].get("plain_text", "No title")
                        break

                # Collect other visible properties
                extras = []
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        continue
                    val = extract_property_value(prop_value)
                    if val not in (None, "", [], False):
                        extras.append(f"{prop_name}: {val}")

                detail = f" | {', '.join(extras)}" if extras else ""
                output += f"{idx}. {entry_title}{detail}\n"

            return output

        return StructuredTool.from_function(
            func=query_database_by_name,
            name="query_database",
            description=(
                "Query a Notion database by its name. "
                "Use 'list_databases' first to see available names."
            ),
            args_schema=QueryDatabaseByNameInput,
        )

    def _create_create_page_tool(self) -> StructuredTool:
        def create_page(
            parent_id: str, title: str, content: Optional[str] = None
        ) -> str:
            children = []
            if content:
                children.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": content}}]
                        },
                    }
                )

            result = self.notion.create_page(
                parent_id, title, children=children if children else None
            )
            return f"Created page '{title}' with ID: {result['id']}"

        return StructuredTool.from_function(
            func=create_page,
            name="create_page",
            description="Create a new page in Notion. Requires a parent page ID and title.",
            args_schema=CreatePageInput,
        )

    def _create_create_entry_tool(self) -> StructuredTool:
        def create_entry(database_name: str, properties_json: str) -> str:
            try:
                properties = json.loads(properties_json)
            except json.JSONDecodeError:
                return "Error: properties_json is not valid JSON"

            db_id = self.notion.get_database_id(database_name)
            if not db_id:
                return f"Database '{database_name}' not found"

            result = self.notion.create_database_entry(db_id, properties)
            return f"Created entry in '{database_name}' with ID: {result['id']}"

        return StructuredTool.from_function(
            func=create_entry,
            name="create_database_entry",
            description=(
                "Create a new entry in a Notion database. "
                "Use 'get_database_schema' first to see required property formats."
            ),
            args_schema=CreateDatabaseEntryInput,
        )
