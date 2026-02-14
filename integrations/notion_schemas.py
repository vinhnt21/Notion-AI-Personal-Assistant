"""Data models for Notion property types.

These helpers build proper Notion API property payloads from simple Python values.
"""

from typing import Any, Dict, List, Optional


def title_property(text: str) -> Dict[str, Any]:
    """Build a title property value"""
    return {"title": [{"text": {"content": text}}]}


def rich_text_property(text: str) -> Dict[str, Any]:
    """Build a rich_text property value"""
    return {"rich_text": [{"text": {"content": text}}]}


def number_property(value: float) -> Dict[str, Any]:
    """Build a number property value"""
    return {"number": value}


def select_property(name: str) -> Dict[str, Any]:
    """Build a select property value"""
    return {"select": {"name": name}}


def multi_select_property(names: List[str]) -> Dict[str, Any]:
    """Build a multi_select property value"""
    return {"multi_select": [{"name": n} for n in names]}


def date_property(
    start: str, end: Optional[str] = None
) -> Dict[str, Any]:
    """Build a date property value (ISO 8601 format)"""
    date_obj: Dict[str, Any] = {"start": start}
    if end:
        date_obj["end"] = end
    return {"date": date_obj}


def checkbox_property(checked: bool) -> Dict[str, Any]:
    """Build a checkbox property value"""
    return {"checkbox": checked}


def url_property(url: str) -> Dict[str, Any]:
    """Build a url property value"""
    return {"url": url}


def email_property(email: str) -> Dict[str, Any]:
    """Build an email property value"""
    return {"email": email}


def status_property(name: str) -> Dict[str, Any]:
    """Build a status property value"""
    return {"status": {"name": name}}


# --- Extractors: pull plain values out of Notion property objects ---


def extract_title(prop: Dict[str, Any]) -> str:
    """Extract plain text from a title property"""
    title_arr = prop.get("title", [])
    if title_arr:
        return title_arr[0].get("plain_text", "")
    return ""


def extract_rich_text(prop: Dict[str, Any]) -> str:
    """Extract plain text from a rich_text property"""
    rt_arr = prop.get("rich_text", [])
    if rt_arr:
        return rt_arr[0].get("plain_text", "")
    return ""


def extract_property_value(prop: Dict[str, Any]) -> Any:
    """Extract a human-readable value from any Notion property object"""
    prop_type = prop.get("type", "")

    if prop_type == "title":
        return extract_title(prop)
    elif prop_type == "rich_text":
        return extract_rich_text(prop)
    elif prop_type == "number":
        return prop.get("number")
    elif prop_type == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    elif prop_type == "multi_select":
        return [s.get("name", "") for s in prop.get("multi_select", [])]
    elif prop_type == "date":
        date_obj = prop.get("date")
        if date_obj:
            return date_obj.get("start", "")
        return ""
    elif prop_type == "checkbox":
        return prop.get("checkbox", False)
    elif prop_type == "url":
        return prop.get("url", "")
    elif prop_type == "email":
        return prop.get("email", "")
    elif prop_type == "status":
        status = prop.get("status")
        return status.get("name", "") if status else ""
    elif prop_type == "formula":
        formula = prop.get("formula", {})
        f_type = formula.get("type", "")
        return formula.get(f_type)
    elif prop_type == "relation":
        return [r.get("id", "") for r in prop.get("relation", [])]
    elif prop_type == "rollup":
        rollup = prop.get("rollup", {})
        r_type = rollup.get("type", "")
        return rollup.get(r_type)
    else:
        return str(prop)
