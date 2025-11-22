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

    async def connect_to_server(self, name: str, server_config: dict):
            """
            Connect to a single MCP server and discover its tools
            
            Args:
                name: Server identifier (e.g., "filesystem", "fetch")
                server_config: Server configuration from server_config.json
            """
            print(f"\n🔌 Connecting to '{name}' server...")
        
            try:
                # Create server parameters from config
                server_params = StdioServerParameters(
                    command=server_config["command"],
                    args=server_config["args"],
                    env=server_config.get("env", None)  # Optional environment variables
                )
                
                # Create stdio client and connect
                stdio_transport = await stdio_client(server_params).__aenter__()
                session = stdio_transport[1]  # Get the ClientSession
                
                # Store the session
                self.sessions[name] = session
                
                # Initialize the session
                await session.initialize()
                
                print(f"✅ Connected to '{name}' server")
                
                # Discover available tools from this server
                await self.discover_tools(name, session)
                
            except Exception as e:
                print(f"❌ Error connecting to '{name}': {str(e)}")
        
                raise

    async def discover_tools(self, server_name: str, session: ClientSession):
            """
            Discover and register tools from an MCP server
            
            Args:
                server_name: Name of the server (e.g., "filesystem")
                session: The MCP session for this server
            """
            print(f"🔍 Discovering tools from '{server_name}'...")
            
            try:
                # Ask the server for its available tools
                tools_list = await session.list_tools()
                
                # Process each tool
                for tool in tools_list.tools:
                    tool_name = tool.name
                    
                    # Map this tool to its server
                    self.tool_to_session[tool_name] = server_name  # ← Populates mapping!
                    
                    # Add to available tools list (Claude API format)
                    self.available_tools.append({  # ← Populates tools list!
                        "name": tool_name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    })
                    
                    print(f"  ✓ Registered tool: {tool_name}")
                
                print(f"✅ Discovered {len(tools_list.tools)} tool(s) from '{server_name}'")
                
            except Exception as e:
                print(f"❌ Error discovering tools from '{server_name}': {str(e)}")
                raise

    async def setup(self):
            """
            Setup the chatbot by loading config and connecting to all servers
            """
            print("\n🚀 Setting up MCP Chatbot...")
            print("=" * 50)
            
            # Load server configuration
            config = self.load_server_config()
            
            # Get all server configurations
            servers = config.get("mcpServers", {})
            
            if not servers:
                print("⚠️  No servers found in configuration!")
                return
            
            # Connect to each server
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
            
            print("\n" + "=" * 50)
            print(f"✅ Setup complete! {len(self.available_tools)} total tools available")
            print("=" * 50)

    async def execute_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Execute a tool by calling the appropriate MCP server
        
        Args:
            tool_name: Name of the tool to execute (e.g., "read_file")
            arguments: Dictionary of arguments for the tool
            
        Returns:
            Tool execution result as string
        """
        try:
            # Find which server has this tool
            server_name = self.tool_to_session.get(tool_name)
            
            if not server_name:
                error_msg = f"❌ Tool '{tool_name}' not found in any connected server"
                print(error_msg)
                return error_msg
            
            # Get the session for this server
            session = self.sessions.get(server_name)
            
            if not session:
                error_msg = f"❌ Server '{server_name}' session not found"
                print(error_msg)
                return error_msg
            
            print(f"🔧 Executing tool '{tool_name}' on '{server_name}' server...")
            print(f"   Arguments: {arguments}")
            
            # Execute the tool via MCP
            result = await session.call_tool(tool_name, arguments)
            
            # Extract the content from the result
            # MCP returns result in a specific format
            if hasattr(result, 'content') and len(result.content) > 0:
                # Get the first content item
                content_item = result.content[0]
                
                # Check if it's text content
                if hasattr(content_item, 'text'):
                    tool_result = content_item.text
                else:
                    tool_result = str(content_item)
            else:
                tool_result = str(result)
            
            print(f"✅ Tool executed successfully")
            return tool_result
            
        except Exception as e:
            error_msg = f"❌ Error executing tool '{tool_name}': {str(e)}"
            print(error_msg)
            return error_msg
        