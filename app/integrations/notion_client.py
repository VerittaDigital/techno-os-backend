"""app/integrations/notion_client.py - Read-only Notion client (fail-closed)."""

import asyncio
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx

# K-SEC: Never log response bodies
logger = logging.getLogger(__name__)

# Env vars (fail-closed if missing)
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ARCONTES_ID = os.getenv("NOTION_DB_ARCONTES_ID")
NOTION_DB_ORDO36_AGENTS_ID = os.getenv("NOTION_DB_ORDO36_AGENTS_ID")
NOTION_DB_AUDIT_ID = os.getenv("NOTION_DB_AUDIT_ID")
NOTION_DB_ACTIONS_ID = os.getenv("NOTION_DB_ACTIONS_ID")
NOTION_DB_EVIDENCE_ID = os.getenv("NOTION_DB_EVIDENCE_ID")
NOTION_DB_PIPELINES_ID = os.getenv("NOTION_DB_PIPELINES_ID")
NOTION_PAGE_DOCS_ID = os.getenv("NOTION_PAGE_DOCS_ID")
NOTION_PAGE_BETA_OPS_ID = os.getenv("NOTION_PAGE_BETA_OPS_ID")
NOTION_PAGE_CICLO_SUPERIOR_ID = os.getenv("NOTION_PAGE_CICLO_SUPERIOR_ID")
NOTION_PAGE_LOGOS_ID = os.getenv("NOTION_PAGE_LOGOS_ID")
NOTION_PAGE_PRINCIPIOS_LOGOS_ID = os.getenv("NOTION_PAGE_PRINCIPIOS_LOGOS_ID")
NOTION_PAGE_NOESIS_ID = os.getenv("NOTION_PAGE_NOESIS_ID")
NOTION_PAGE_SYNCHRONOS_ID = os.getenv("NOTION_PAGE_SYNCHRONOS_ID")
NOTION_PAGE_NUCLEO_INTERNO_ID = os.getenv("NOTION_PAGE_NUCLEO_INTERNO_ID")

# Required envs
REQUIRED_ENVS = [
    "NOTION_TOKEN", "NOTION_DB_ARCONTES_ID", "NOTION_DB_ORDO36_AGENTS_ID",
    "NOTION_DB_AUDIT_ID", "NOTION_DB_ACTIONS_ID", "NOTION_DB_EVIDENCE_ID", "NOTION_DB_PIPELINES_ID"
]

# Redaction patterns for Tier-2
REDACTION_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***'),  # emails
    (r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '***.***.***-**'),  # CPF-like
    (r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', '**.***.***/****-**'),  # CNPJ-like
    (r'\b\d{10,11}\b', '***********'),  # phone-like
    (r'Authorization:\s*Bearer\s+[A-Za-z0-9._=-]{16,}', 'Authorization: Bearer ***REDACTED***'),
    (r'X-API-Key:\s*[A-Za-z0-9._=-]{12,}', 'X-API-Key: ***REDACTED***'),
    (r'\b[A-Za-z0-9_-]{20,}\b', '***REDACTED***'),  # high entropy tokens
    (r'[?&](token|apikey|signature)=[^&\s]+', '?***=***REDACTED***'),  # URL params
]

# Simple cache (in-memory, TTL 60s)
_cache: Dict[str, Dict[str, Any]] = {}

def _is_cached(key: str) -> bool:
    if key not in _cache:
        return False
    if time.time() - _cache[key]['timestamp'] > 60:
        del _cache[key]
        return False
    return True

def _get_cached(key: str) -> Any:
    return _cache[key]['data']

def _set_cache(key: str, data: Any):
    _cache[key] = {'data': data, 'timestamp': time.time()}

def redact_text(text: str) -> str:
    """Apply redaction patterns to text."""
    for pattern, replacement in REDACTION_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text

def truncate_preview(text: str, max_chars: int = 120) -> str:
    """Truncate to max_chars after redaction."""
    redacted = redact_text(text)
    if len(redacted) <= max_chars:
        return redacted
    return redacted[:max_chars] + '...'

class NotionClient:
    def __init__(self):
        self.token = NOTION_TOKEN
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        self.timeout = httpx.Timeout(10.0)  # 10s timeout

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    await asyncio.sleep(int(retry_after))
                    return await self._request(method, endpoint, **kwargs)
                else:
                    raise Exception("Rate limited")
            response.raise_for_status()
            return response.json()

    async def query_database(self, db_id: str, filter: Optional[Dict] = None) -> List[Dict]:
        cache_key = f"db_{db_id}_{filter}"
        if _is_cached(cache_key):
            return _get_cached(cache_key)
        body = {"filter": filter} if filter else {}
        data = await self._request("POST", f"/databases/{db_id}/query", json=body)
        results = data.get("results", [])
        _set_cache(cache_key, results)
        return results

    async def get_page(self, page_id: str) -> Dict:
        cache_key = f"page_{page_id}"
        if _is_cached(cache_key):
            return _get_cached(cache_key)
        data = await self._request("GET", f"/pages/{page_id}")
        _set_cache(cache_key, data)
        return data

    async def get_block_children(self, block_id: str) -> List[Dict]:
        cache_key = f"blocks_{block_id}"
        if _is_cached(cache_key):
            return _get_cached(cache_key)
        data = await self._request("GET", f"/blocks/{block_id}/children")
        results = data.get("results", [])
        _set_cache(cache_key, results)
        return results

# Global client instance
client = NotionClient()

# Sanitize functions
def sanitize_tier1(item: Dict) -> Dict:
    """Return only safe Tier-1 fields."""
    # Placeholder: assume properties like 'Name', 'Status', etc.
    return {k: v for k, v in item.get('properties', {}).items() if k in ['Name', 'Status', 'ID']}

def sanitize_tier2(item: Dict) -> Dict:
    """Preview for free-text fields."""
    sanitized = {}
    for k, v in item.get('properties', {}).items():
        if isinstance(v, dict) and 'rich_text' in v:
            text = ''.join([t['plain_text'] for t in v['rich_text']])
            sanitized[k] = truncate_preview(text)
        else:
            sanitized[k] = v
    return sanitized

def sanitize_attachments(item: Dict) -> List[Dict]:
    """Tier-3: metadata only."""
    attachments = []
    for prop in item.get('properties', {}).values():
        if isinstance(prop, dict) and prop.get('type') == 'files':
            for file in prop.get('files', []):
                attachments.append({
                    'filename': file.get('name', 'unknown'),
                    'mime_type': file.get('type', 'unknown'),
                    'size': file.get('size', 0),
                    'last_modified': file.get('last_edited_time'),
                    'notion_url': f"https://www.notion.so/{item['id'].replace('-', '')}"
                })
    return attachments

def sanitize_relations(item: Dict) -> List[Dict]:
    """Tier-4: titles only."""
    relations = []
    for prop in item.get('properties', {}).values():
        if isinstance(prop, dict) and prop.get('type') == 'relation':
            for rel in prop.get('relation', []):
                relations.append({'title': rel.get('title', 'unknown')})
    return relations

# Endpoint helpers
async def get_agents() -> List[Dict]:
    if not NOTION_DB_ORDO36_AGENTS_ID:
        raise Exception("MISSING_CONFIG")
    items = await client.query_database(NOTION_DB_ORDO36_AGENTS_ID)
    return [{
        'tier1': sanitize_tier1(item),
        'tier2': sanitize_tier2(item),
        'attachments': sanitize_attachments(item),
        'relations': sanitize_relations(item),
        'notion_url': f"https://www.notion.so/{item['id'].replace('-', '')}"
    } for item in items]

# Similar for others, but for brevity, implement one fully.

async def get_arcontes() -> List[Dict]:
    if not NOTION_DB_ARCONTES_ID:
        raise Exception("MISSING_CONFIG")
    items = await client.query_database(NOTION_DB_ARCONTES_ID)
    return [{
        'tier1': sanitize_tier1(item),
        'tier2': sanitize_tier2(item),
        'attachments': sanitize_attachments(item),
        'relations': sanitize_relations(item),
        'notion_url': f"https://www.notion.so/{item['id'].replace('-', '')}"
    } for item in items]

async def get_audit() -> List[Dict]:
    if not NOTION_DB_AUDIT_ID:
        raise Exception("MISSING_CONFIG")
    items = await client.query_database(NOTION_DB_AUDIT_ID)
    return [{
        'tier1': sanitize_tier1(item),
        'tier2': sanitize_tier2(item),
        'attachments': sanitize_attachments(item),
        'relations': sanitize_relations(item),
        'notion_url': f"https://www.notion.so/{item['id'].replace('-', '')}"
    } for item in items]

# Placeholder for others
async def get_actions() -> List[Dict]:
    if not NOTION_DB_ACTIONS_ID:
        raise Exception("MISSING_CONFIG")
    items = await client.query_database(NOTION_DB_ACTIONS_ID)
    return [{'tier1': sanitize_tier1(item), 'notion_url': f"https://www.notion.so/{item['id'].replace('-', '')}"} for item in items]

async def get_evidence() -> List[Dict]:
    if not NOTION_DB_EVIDENCE_ID:
        raise Exception("MISSING_CONFIG")
    items = await client.query_database(NOTION_DB_EVIDENCE_ID)
    return [{'tier1': sanitize_tier1(item), 'notion_url': f"https://www.notion.so/{item['id'].replace('-', '')}"} for item in items]

async def get_pipelines() -> List[Dict]:
    if not NOTION_DB_PIPELINES_ID:
        raise Exception("MISSING_CONFIG")
    items = await client.query_database(NOTION_DB_PIPELINES_ID)
    return [{'tier1': sanitize_tier1(item), 'notion_url': f"https://www.notion.so/{item['id'].replace('-', '')}"} for item in items]

async def get_docs() -> List[Dict]:
    if not NOTION_PAGE_DOCS_ID:
        raise Exception("MISSING_CONFIG")
    page = await client.get_page(NOTION_PAGE_DOCS_ID)
    blocks = await client.get_block_children(NOTION_PAGE_DOCS_ID)
    # Placeholder: extract child pages
    docs = [{'title': block.get('child_page', {}).get('title', 'unknown'), 'notion_url': f"https://www.notion.so/{block['id'].replace('-', '')}"} for block in blocks if block.get('type') == 'child_page']
    return docs

async def get_governance() -> List[Dict]:
    # Placeholder: list of pages
    pages = []
    if NOTION_PAGE_CICLO_SUPERIOR_ID:
        pages.append({'title': 'Ciclo Superior', 'notion_url': f"https://www.notion.so/{NOTION_PAGE_CICLO_SUPERIOR_ID.replace('-', '')}"})
    # Add others similarly
    return pages