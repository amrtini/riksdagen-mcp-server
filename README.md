# Riksdagen MCP Server

This project implements a Model Context Protocol (MCP) server that allows Claude to search the Swedish Parliament (Riksdagen) document archive and retrieve URLs in JSON format.
The project is generetad using Claude 3.7. 

## Overview

The Riksdagen MCP server provides tools for searching documents in the Swedish Parliament's open data archive. It allows Claude to:

1. Search for documents based on various criteria (keywords, document types, dates, etc.)
2. Get a list of available document types
3. Create lists of URLs for specific documents in various formats (JSON, HTML, text)

## Prerequisites

- Python 3.9+
- FastAPI
- Uvicorn
- MCP Python SDK
- httpx

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/amrtini/riksdagen-mcp-server.git
   cd riksdagen-mcp-server
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install fastapi uvicorn httpx mcp
   ```

   Note: You might need to install the MCP Python SDK directly from its repository:
   ```
   pip install git+https://github.com/modelcontextprotocol/python-sdk.git
   ```

## Running the Server

1. Start the MCP server:
   ```
   uvicorn mcp_riksdagen_server:app --host 0.0.0.0 --port 8000 --reload
   ```

2. The server will be available at http://localhost:8000

## MCP Tools

The server provides the following MCP tools:

### 1. riksdagen_search

Search for documents in the Riksdagen archive based on various criteria.

**Parameters:**
- `sok`: Search term (optional)
- `doktyp`: Document type (optional, e.g. "prop", "mot", "bet")
- `rm`: Parliamentary year (optional, e.g. "2021/22")
- `from_date`: From date in YYYY-MM-DD format (optional)
- `tom`: To date in YYYY-MM-DD format (optional)
- `sort`: Sort order (optional, default: "rel", options: "rel", "datum", "beteckning")
- `sortorder`: Sort direction (optional, default: "desc", options: "desc", "asc")
- `limit`: Maximum number of results to return (optional, default: 10)

**Returns:**
A JSON object containing document URLs and metadata.

### 2. riksdagen_get_document_types

Get a list of available document types in the Riksdagen archive.

**Returns:**
A dictionary mapping document type codes to their descriptions.

### 3. riksdagen_create_url_list

Create a list of URLs for Riksdagen documents in the specified format.

**Parameters:**
- `document_ids`: List of document IDs
- `format`: Format of the documents (default: "json", options: "json", "html", "text")

**Returns:**
A JSON object containing document URLs.

## Using with Claude

Claude can use this MCP server to search for documents in the Riksdagen archive and generate URL lists for further processing. The example client demonstrates how to interact with the server.

### Example Claude Prompt

```
I want to search for documents in the Swedish Parliament archive about climate change (klimat in Swedish) from the last year. Can you help me find relevant motions and create a list of URLs to access them?
```

Claude can then use the MCP tools to:
1. Search for documents with the term "klimat"
2. Filter for motion documents (doktyp="mot")
3. Set the parliamentary year to the current one
4. Create a list of URLs for the found documents

## Using the Client

The included client demonstrates how to interact with the MCP server programmatically:

```python
# Create the client
client = ClaudeRiksdagenClient()

# Search for documents
search_results = await client.search_documents(
    search_term="klimat",
    document_type="mot",
    parliamentary_year="2023/24",
    limit=5
)

# Create URL list for the found documents
doc_ids = [doc["id"] for doc in search_results["documents"]]
url_list = await client.create_url_list(doc_ids, format="json")
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Swedish Parliament (Riksdagen) for providing the open data API
- The Model Context Protocol (MCP) team for developing the standard
