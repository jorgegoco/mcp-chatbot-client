import asyncio
import json
import os
from typing import Dict, List, Any

# Environment variables
from dotenv import load_dotenv

# Anthropic API
from anthropic import Anthropic

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# For nested async (remember our discussion!)
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables from .env
load_dotenv()