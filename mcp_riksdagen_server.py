"""
MCP Server for Riksdagen Archive Search

This script creates a Model Context Protocol (MCP) server that allows Claude to search
the Swedish Parliament (Riksdagen) document archive and retrieve URLs in JSON format.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import httpx
import asyncio
from mcp.server.fastmcp import FastMCP, Context

@dataclass
class RiksdagenSearchParams:
    """Parameters for searching the Riksdagen document archive."""
    
    sok: Optional[str] = None                # Search term
    doktyp: Optional[str] = None             # Document type
    rm: Optional[str] = None                 # Parliamentary year
    from_date: Optional[str] = None          # From date (YYYY-MM-DD)
    tom: Optional[str] = None                # To date (YYYY-MM-DD)
    ts: Optional[str] = None                 # Time span
    bet: Optional[str] = None                # Designation
    tempbet: Optional[str] = None            # Temporary designation
    nr: Optional[str] = None                 # Number
    org: Optional[str] = None                # Organization
    iid: Optional[str] = None                # ID
    webbtv: Optional[str] = None             # Web TV
    talare: Optional[str] = None             # Speaker
    exakt: Optional[str] = None              # Exact search
    planering: Optional[str] = None          # Planning
    sort: str = "rel"                        # Sort order (rel, datum, beteckning, publikation)
    sortorder: str = "desc"                  # Sort direction (desc, asc)
    rapport: Optional[str] = None            # Report
    utformat: str = "json"                   # Output format (json, xml, etc.)
    a: Optional[str] = None                  # Additional param
    
    def to_query_params(self) -> Dict[str, str]:
        """Convert parameters to query parameters dictionary."""
        params = {}
        for key, value in self.__dict__.items():
            if value is not None:
                # Handle the 'from_date' parameter which needs to be renamed to 'from'
                if key == "from_date":
                    params["from"] = value
                else:
                    params[key] = value
        return params


class RiksdagenClient:
    """Client for interacting with the Riksdagen API."""
    
    BASE_URL = "https://data.riksdagen.se"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_documents(self, params: RiksdagenSearchParams) -> Dict[str, Any]:
        """Search for documents based on the provided parameters."""
        endpoint = f"{self.BASE_URL}/dokumentlista/"
        
        try:
            response = await self.client.get(endpoint, params=params.to_query_params())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Error searching Riksdagen documents: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Initialize the Riksdagen client
riksdagen_client = RiksdagenClient()

# Define the lifespan context manager
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def riksdagen_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Handle server startup and shutdown."""
    try:
        # Any initialization can go here
        yield None
    finally:
        # Clean up resources when the server shuts down
        await riksdagen_client.close()

# Create the FastMCP server with the lifespan
mcp = FastMCP("Riksdagen Archive Search", lifespan=riksdagen_lifespan)


@mcp.tool()
async def riksdagen_search(
    sok: Optional[str] = None,
    doktyp: Optional[str] = None,
    rm: Optional[str] = None,
    from_date: Optional[str] = None,
    tom: Optional[str] = None,
    sort: str = "rel",
    sortorder: str = "desc",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for documents in the Riksdagen archive.
    
    Parameters:
    - sok: Search term (optional)
    - doktyp: Document type (optional, e.g. "prop", "mot", "bet")
    - rm: Parliamentary year (optional, e.g. "2021/22")
    - from_date: From date in YYYY-MM-DD format (optional)
    - tom: To date in YYYY-MM-DD format (optional)
    - sort: Sort order (optional, default: "rel", options: "rel", "datum", "beteckning")
    - sortorder: Sort direction (optional, default: "desc", options: "desc", "asc")
    - limit: Maximum number of results to return (optional, default: 10)
    
    Returns:
    A JSON object containing document URLs and metadata
    """
    params = RiksdagenSearchParams(
        sok=sok,
        doktyp=doktyp,
        rm=rm,
        from_date=from_date,
        tom=tom,
        sort=sort,
        sortorder=sortorder,
        utformat="json"
    )
    
    results = await riksdagen_client.search_documents(params)
    
    # Extract document list
    documents = []
    if "dokumentlista" in results and "dokument" in results["dokumentlista"]:
        raw_docs = results["dokumentlista"]["dokument"]
        # Ensure we don't exceed the limit
        for doc in raw_docs[:limit]:
            documents.append({
                "id": doc.get("id", ""),
                "title": doc.get("titel", ""),
                "type": doc.get("typ", ""),
                "document_type": doc.get("doktyp", ""),
                "date": doc.get("datum", ""),
                "published": doc.get("publicerad", ""),
                "parliamentary_year": doc.get("rm", ""),
                "organization": doc.get("organ", ""),
                "text_url": doc.get("dokument_url_text", ""),
                "html_url": doc.get("dokument_url_html", ""),
                "status": doc.get("status", "")
            })
    
    # Create response in the required format
    response = {
        "total_hits": int(results.get("dokumentlista", {}).get("@traffar", "0")),
        "documents": documents
    }
    
    return response


@mcp.tool()
def riksdagen_get_document_types() -> Dict[str, str]:
    """
    Get a list of available document types in the Riksdagen archive.
    
    Returns:
    A dictionary mapping document type codes to their descriptions
    """
    # These are the common document types in the Riksdagen archive
    document_types = {
        "prop": "Government Bill (Proposition)",
        "mot": "Motion",
        "bet": "Committee Report (Betänkande)",
        "prot": "Protocol",
        "skr": "Government Communication (Skrivelse)",
        "sou": "Official Government Report (Statens offentliga utredningar)",
        "ds": "Ministry Publication (Departementsserien)",
        "fpm": "Factual Memorandum (Faktapromemoria)",
        "utl": "Statement (Utlåtande)",
        "dir": "Committee Directive (Kommittédirektiv)",
        "rskr": "Parliamentary Communication (Riksdagsskrivelse)",
        "ip": "Interpellation",
        "fr": "Question (Fråga)",
        "EU": "EU Document"
    }
    
    return document_types


@mcp.tool()
def riksdagen_create_url_list(
    document_ids: List[str],
    format: str = "json"
) -> Dict[str, Any]:
    """
    Create a list of URLs for Riksdagen documents in the specified format.
    
    Parameters:
    - document_ids: List of document IDs
    - format: Format of the documents (default: "json", options: "json", "html", "text")
    
    Returns:
    A JSON object containing document URLs
    """
    format_extension = format.lower()
    
    # Validate format
    if format_extension not in ["json", "html", "text"]:
        raise ValueError("Invalid format. Supported formats are: json, html, text")
    
    # Create URLs for each document ID
    urls = []
    for doc_id in document_ids:
        if format_extension == "json":
            # For JSON format, we need to use the API endpoint
            url = f"https://data.riksdagen.se/dokument/{doc_id}.{format_extension}"
        else:
            # For HTML and text formats, use the document URL
            url = f"https://data.riksdagen.se/dokument/{doc_id}.{format_extension}"
        
        urls.append({
            "id": doc_id,
            "url": url
        })
    
    return {
        "urls": urls,
        "format": format_extension,
        "count": len(urls)
    }





if __name__ == "__main__":
    # Run the server
    mcp.run()