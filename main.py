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


class MCPChatbot:
    def __init__(self):
        """Initialize the chatbot with empty state"""
        # Store all MCP sessions (one per server)
        self.sessions: Dict[str, ClientSession] = {}
        
        # Map tool names to their server sessions
        self.tool_to_session: Dict[str, str] = {}
        
        # List of all available tools (formatted for Claude API)
        self.available_tools: List[Dict[str, Any]] = []
        
        # Anthropic client for Claude API
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        
        print("✅ MCPChatbot initialized!")

        def load_server_config(self, config_path: str = "server_config.json") -> dict:
            """
            Load MCP server configuration from JSON file
            
            Args:
                config_path: Path to the server config file
                
            Returns:
                Dictionary with server configurations
            """
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    print(f"✅ Loaded configuration from {config_path}")
                    print(f"📋 Found {len(config.get('mcpServers', {}))} server(s)")
                    return config
            except FileNotFoundError:
                print(f"❌ Error: {config_path} not found!")
                print("💡 Make sure server_config.json exists in the same directory")
                raise
            except json.JSONDecodeError as e:
                print(f"❌ Error: Invalid JSON in {config_path}")
                print(f"💡 {str(e)}")
                raise