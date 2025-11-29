import asyncio
import json
import os
from typing import Dict, List, Any
from contextlib import AsyncExitStack

# Environment variables
from dotenv import load_dotenv

# Anthropic API
from anthropic import Anthropic

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# For nested async
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables from .env
load_dotenv()


class MCPChatbot:
    def __init__(self):
        """Initialize the chatbot with empty state"""
        # Anthropic client for Claude API
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Store sessions during runtime (populated when servers connect)
        self.sessions: Dict[str, ClientSession] = {}
        
        # Map tool names to their server sessions
        self.tool_to_session: Dict[str, ClientSession] = {}
        
        # List of all available tools (formatted for Claude API)
        self.available_tools: List[Dict[str, Any]] = []
        
        print("✅ MCPChatbot initialized!")
    
    def load_server_config(self, config_path: str = "server_config.json") -> dict:
        """Load MCP server configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"✅ Loaded configuration from {config_path}")
                print(f"📋 Found {len(config.get('mcpServers', {}))} server(s)")
                return config
        except FileNotFoundError:
            print(f"❌ Error: {config_path} not found!")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {config_path}")
            print(f"💡 {str(e)}")
            raise
    
    async def process_query(self, query: str):
        """Process a single user query with Claude"""
        messages = [{'role': 'user', 'content': query}]
        
        response = self.anthropic.messages.create(
            max_tokens=4096,
            model='claude-haiku-4-5-20251001',
            tools=self.available_tools,
            messages=messages
        )
        
        process_query = True
        
        while process_query:
            assistant_content = []
            
            for content in response.content:
                if content.type == 'text':
                    print(content.text)
                    assistant_content.append(content)
                    if len(response.content) == 1:
                        process_query = False
                        
                elif content.type == 'tool_use':
                    assistant_content.append(content)
                    messages.append({'role': 'assistant', 'content': assistant_content})
                    
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name
                    
                    print(f"\n🔧 Calling tool '{tool_name}' with args: {tool_args}")
                    
                    # Find which server has this tool
                    session = self.tool_to_session.get(tool_name)
                    if not session:
                        result_content = f"Error: Tool '{tool_name}' not found"
                    else:
                        # Get the session and call the tool
                        result = await session.call_tool(tool_name, arguments=tool_args)
                        result_content = result.content
                    
                    print(f"✅ Tool executed\n")
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_content
                        }]
                    })
                    
                    # Get Claude's next response
                    response = self.anthropic.messages.create(
                        max_tokens=4096,
                        model='claude-haiku-4-5-20251001',
                        tools=self.available_tools,
                        messages=messages
                    )
                    
                    if len(response.content) == 1 and response.content[0].type == "text":
                        print(response.content[0].text)
                        process_query = False
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\n" + "=" * 50)
        print("🤖 MCP Chatbot Ready!")
        print("=" * 50)
        print("Type your message and press Enter")
        print("Type 'quit' or 'exit' to end the conversation")
        print("Type 'tools' to see available tools")
        print("=" * 50 + "\n")
        
        while True:
            try:
                query = input("You: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if query.lower() == 'tools':
                    self.show_available_tools()
                    continue
                
                if not query:
                    continue
                
                await self.process_query(query)
                print("\n")
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
    
    def show_available_tools(self):
        """Display all available tools"""
        print("\n📋 Available Tools:")
        print("=" * 50)
        
        if not self.available_tools:
            print("No tools available")
            return
        
        # Group tools by server
        tools_by_server = {}
        for tool_name, server_name in self.tool_to_session.items():
            if server_name not in tools_by_server:
                tools_by_server[server_name] = []
            tools_by_server[server_name].append(tool_name)
        
        # Display grouped tools
        for server_name, tools in tools_by_server.items():
            print(f"\n🔌 {server_name} server:")
            for tool in tools:
                tool_info = next((t for t in self.available_tools if t["name"] == tool), None)
                if tool_info:
                    print(f"   • {tool} - {tool_info.get('description', 'No description')}")
        
        print("=" * 50 + "\n")
    
    async def connect_to_servers_and_run(self):
        """
        Connect to all MCP servers and run the chat loop.
        Uses AsyncExitStack for scalable management of multiple servers.
        """
        print("\n🚀 Setting up MCP Chatbot...")
        print("=" * 50)
        
        # Load configuration
        config = self.load_server_config()
        servers = config.get("mcpServers", {})
        
        if not servers:
            print("⚠️  No servers found in configuration!")
            return
        
        # Use AsyncExitStack to manage multiple contexts dynamically
        async with AsyncExitStack() as stack:
            # Connect to each server
            for server_name, server_config in servers.items():
                print(f"\n🔌 Connecting to '{server_name}' server...")
                
                try:
                    # Create server parameters
                    server_params = StdioServerParameters(
                        command=server_config["command"],
                        args=server_config["args"],
                        env=server_config.get("env", None)
                    )
                    
                    # Enter the stdio_client context and keep it in the stack
                    read, write = await stack.enter_async_context(
                        stdio_client(server_params)
                    )
                    
                    # Enter the ClientSession context and keep it in the stack
                    session = await stack.enter_async_context(
                        ClientSession(read, write)
                    )
                    
                    # Initialize the session
                    await session.initialize()
                    
                    # Store the session
                    self.sessions[server_name] = session
                    
                    # Discover tools from this server
                    response = await session.list_tools()
                    
                    for tool in response.tools:
                        self.tool_to_session[tool.name] = session
                        self.available_tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        })
                    
                    print(f"✅ Connected to '{server_name}' with {len(response.tools)} tool(s)")
                    
                except Exception as e:
                    print(f"❌ Error connecting to '{server_name}': {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other servers even if one fails
                    continue
            
            # Check if we have any connected servers
            if not self.sessions:
                print("\n❌ No servers connected successfully!")
                return
            
            print("\n" + "=" * 50)
            print(f"✅ Setup complete! {len(self.available_tools)} total tools available")
            print("=" * 50)
            
            # Run chat loop - all contexts stay alive here!
            await self.chat_loop()
            
            # When we exit this block, AsyncExitStack automatically closes
            # all contexts in reverse order