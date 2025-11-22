# MCP Chatbot Client - Complete Learning Guide

> **Project:** Building an MCP chatbot client that connects to external MCP servers  
> **Date Started:** November 20, 2024  
> **Status:** In Progress (Steps 1-9 completed)

---

## 📑 Table of Contents

1. [Project Overview](#project-overview)
2. [What is MCP?](#what-is-mcp)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Deep Dive: Key Concepts](#deep-dive-key-concepts)
5. [Code Structure & Explanation](#code-structure--explanation)
6. [Important Q&A Sessions](#important-qa-sessions)
7. [Security Considerations](#security-considerations)
8. [What's Next](#whats-next)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

### Goals

- Build a chatbot that connects to **external MCP servers** (not creating our own servers)
- Use it as a **learning playground** to understand MCP
- Connect to Anthropic's reference servers (filesystem, fetch)
- Learn by doing - replicate each step in VSCode IDE
- Use `uv` for Python project management

### Based On

DeepLearning.AI Course: "MCP: Build Rich-Context AI Apps with Anthropic"  
Repository: https://github.com/jorgegoco/mcp_build_rich_context_ai_apps_with_anthropic

### Key Difference from Course

- **Course:** Build your own MCP servers + connect to them
- **Our Project:** Connect to existing external servers (Lesson 6 focus)

---

## 🌐 What is MCP?

### The Problem MCP Solves

**Before MCP: The M×N Problem**

```
5 AI Apps × 10 Tools = 50 custom integrations needed! 😱

Each AI app needs custom code for each tool:
- Claude Desktop → GitHub (custom integration)
- Claude Desktop → Slack (custom integration)
- VSCode → GitHub (custom integration)
- VSCode → Slack (custom integration)
... and so on
```

**With MCP: The M+N Solution**

```
5 AI Apps + 10 Tools = 15 integrations total! 🎉

- 5 AI apps each implement ONE MCP client
- 10 tools each implement ONE MCP server
- Everything works together through the standard protocol
```

### MCP Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP HOST                              │
│              (Your AI Application)                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ MCP Client 1 │  │ MCP Client 2 │  │ MCP Client 3 │  │
│  │ (filesystem) │  │   (fetch)    │  │   (github)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          │ One-to-one       │ One-to-one      │ One-to-one
          │ connection       │ connection      │ connection
          │                  │                  │
┌─────────▼──────────┐ ┌─────▼─────────┐ ┌────▼──────────┐
│  MCP Server 1      │ │ MCP Server 2  │ │ MCP Server 3  │
│  (Filesystem Ops)  │ │ (Web Fetch)   │ │ (GitHub API)  │
└────────────────────┘ └───────────────┘ └───────────────┘
```

### Core Components

1. **MCP Host:** Your AI application (the chatbot we're building)
2. **MCP Client:** Manages connection to ONE server
3. **MCP Server:** Provides tools/resources/prompts
4. **Protocol:** JSON-RPC 2.0 over stdio (local) or HTTP/SSE (remote)

---

## 🚀 Step-by-Step Setup

### ✅ Step 1: Project Name

**Decided on:** `mcp-chatbot-client`

**Reasoning:**

- Clear and descriptive
- Indicates it's a **client** (not a server)
- Different from similar projects

---

### ✅ Step 2: Initialize Project

```bash
uv init
```

**What was created:**

```
mcp-chatbot-client/
├── .git/
├── .gitignore
├── .python-version  (3.13)
├── README.md
├── main.py
└── pyproject.toml
```

---

### ✅ Step 3: Understanding Dependencies

#### Core Dependencies Needed

1. **`anthropic`** - Claude API client
   - Purpose: Send messages to Claude and get responses
2. **`mcp`** - Model Context Protocol SDK
   - Purpose: Create MCP clients and connect to servers
3. **`python-dotenv`** - Environment variable loader
   - Purpose: Load API keys from .env file securely
4. **`nest-asyncio`** - Nested async support
   - Purpose: Allow nested event loops (MCP uses async heavily)

#### Why nest-asyncio?

**The Problem:**
Python normally doesn't allow running an event loop inside another event loop.

**JavaScript Equivalent:**
Imagine if you couldn't use `await` inside an already-awaited function!

**What nest-asyncio does:**
Patches asyncio to be more permissive (like JavaScript)

**When needed:**

- Jupyter notebooks: YES
- Interactive environments: YES
- Regular scripts: Usually no, but harmless
- Our MCP project: YES (multiple async connections)

---

### ✅ Step 4: Install Dependencies

```bash
uv add anthropic
uv add mcp
uv add python-dotenv
uv add nest-asyncio
```

**Result in pyproject.toml:**

```toml
[project]
name = "mcp-chatbot-client"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "anthropic>=0.74.1",
    "mcp>=1.21.2",
    "nest-asyncio>=1.6.0",
    "python-dotenv>=1.2.1",
]
```

---

### ✅ Step 5: Setup .env File

**Create the file:**

```bash
touch .env
```

**Add your API key:**

```bash
ANTHROPIC_API_KEY=your_actual_api_key_here
```

**CRITICAL SECURITY FIX:**

```bash
# Add .env to .gitignore
echo ".env" >> .gitignore
```

**Why this matters:**

- Without this, your API key could be committed to Git
- Public repositories would expose your key
- Anyone could use your API credits

**Your .gitignore should include:**

```
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

# Environment variables (IMPORTANT!)
.env
```

---

### ✅ Step 6: Understanding Server Configuration

#### The server_config.json File

This file tells your chatbot **which MCP servers to connect to**.

**Structure:**

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["argument1", "argument2"],
      "env": {
        "OPTIONAL_ENV_VAR": "value"
      }
    }
  }
}
```

#### How This Enables Standardization

**The Three Layers:**

```
Layer 1: Discovery (server_config.json)
├─ Standard format all MCP clients understand
└─ Tells how to launch servers

Layer 2: Transport (stdio or HTTP/SSE)
├─ Local: stdin/stdout (what we use)
└─ Remote: HTTP/SSE

Layer 3: Protocol (JSON-RPC 2.0)
├─ initialize - Handshake
├─ tools/list - Discover tools
├─ tools/call - Execute tool
├─ resources/list - Discover resources
└─ prompts/list - Discover prompts
```

**Why standardization matters:**

This SAME config file works with:

- Your Python chatbot
- Claude Desktop
- Cursor IDE
- Windsurf
- Any MCP-compatible app!

---

### ✅ Step 7: Create server_config.json

```bash
touch server_config.json
```

**Content:**

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

**What each server does:**

| Server     | Command       | Purpose                       | Access                  |
| ---------- | ------------- | ----------------------------- | ----------------------- |
| filesystem | npx (Node.js) | Read/write files              | Current directory (`.`) |
| fetch      | uvx (Python)  | Fetch web content as markdown | Any URL                 |

---

### ✅ Step 8: Understanding Chatbot Architecture

#### The Big Picture

```
┌──────────────────────────────────────────────────────────┐
│                    YOUR CHATBOT                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Load Configuration (server_config.json)        │  │
│  └────────────────────────────────────────────────────┘  │
│                          ↓                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  2. Create MCP Clients (one per server)            │  │
│  │     - Connect to "filesystem" server               │  │
│  │     - Connect to "fetch" server                    │  │
│  └────────────────────────────────────────────────────┘  │
│                          ↓                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  3. Discover Tools from all servers                │  │
│  │     - filesystem: read_file, write_file, etc.      │  │
│  │     - fetch: fetch_url                             │  │
│  └────────────────────────────────────────────────────┘  │
│                          ↓                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  4. Conversation Loop                              │  │
│  │     User → Claude → Tool Call → Server → Result   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

#### Detailed Conversation Flow

**Example: User asks to read a file and fetch a website**

```
Step 1: User Input
├─ "Read the README.md file and fetch https://example.com"
│
Step 2: Send to Claude API
├─ Message: User's request
├─ Tools: All discovered tools from MCP servers
│   ├─ read_file (from filesystem)
│   ├─ write_file (from filesystem)
│   └─ fetch_url (from fetch)
│
Step 3: Claude Responds with Tool Calls
├─ Tool Call 1: read_file
│   └─ Arguments: { "path": "README.md" }
├─ Tool Call 2: fetch_url
│   └─ Arguments: { "url": "https://example.com" }
│
Step 4: Execute Tools via MCP Servers
├─ Send to filesystem server: read_file("README.md")
│   └─ Result: "# MCP Chatbot Client\n..."
├─ Send to fetch server: fetch_url("https://example.com")
│   └─ Result: "Example Domain\nThis domain..."
│
Step 5: Send Results Back to Claude
├─ Tool Results added to conversation
│
Step 6: Claude Final Response
└─ "I've read your README and fetched the website. Here's what I found..."
```

#### Core Components

```python
class MCPChatbot:
    def __init__(self):
        self.sessions = {}           # Store MCP sessions
        self.tool_to_session = {}    # Map tools to servers
        self.available_tools = []    # Tools for Claude
        self.anthropic = Anthropic() # Claude API client
        self.conversation_history = [] # Full conversation
```

---

### ✅ Step 9: Writing the Chatbot Code

#### File Structure

```
mcp-chatbot-client/
├── .env                    # API key (git-ignored)
├── server_config.json      # MCP servers config
├── main.py                 # Entry point (original, now renamed to chatbot.py)
└── chatbot.py             # Main chatbot class
```

#### Complete Code (So Far)

**chatbot.py:**

```python
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

# For nested async
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
                env=server_config.get("env", None)
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
                self.tool_to_session[tool_name] = server_name

                # Add to available tools list (Claude API format)
                self.available_tools.append({
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
```

#### When Dictionaries Get Populated

```
Timeline:

1. __init__() called
   ├─ sessions = {}
   ├─ tool_to_session = {}
   └─ available_tools = []

2. setup() called
   └─ load_server_config()
       └─ Returns config dictionary

3. connect_to_server("filesystem", {...})
   ├─ Launch: npx -y @modelcontextprotocol/server-filesystem .
   ├─ sessions["filesystem"] = <Session>  ✓ POPULATED
   └─ discover_tools("filesystem", session)
       ├─ Server responds with tools: read_file, write_file, etc.
       ├─ tool_to_session["read_file"] = "filesystem"  ✓ POPULATED
       ├─ tool_to_session["write_file"] = "filesystem"  ✓ POPULATED
       ├─ available_tools.append({...})  ✓ POPULATED
       └─ available_tools.append({...})  ✓ POPULATED

4. connect_to_server("fetch", {...})
   ├─ Launch: uvx mcp-server-fetch
   ├─ sessions["fetch"] = <Session>  ✓ POPULATED
   └─ discover_tools("fetch", session)
       ├─ Server responds with tools: fetch_url
       ├─ tool_to_session["fetch_url"] = "fetch"  ✓ POPULATED
       └─ available_tools.append({...})  ✓ POPULATED

5. Ready for chat!
   ├─ All sessions connected
   ├─ All tools mapped
   └─ Ready to handle user requests
```

---

## 🧠 Deep Dive: Key Concepts

### Local vs Remote MCP Servers

#### Local Subprocess Servers (What We're Using)

```
Your Machine
┌─────────────────────────────────┐
│  Chatbot Process                │
│    │                             │
│    │ spawns subprocess           │
│    ▼                             │
│  Filesystem Server (npx ran)    │
│    ▲                             │
│    │ stdio pipes                 │
│    │ (stdin/stdout)              │
│    ▼                             │
│  Chatbot Process                │
└─────────────────────────────────┘
```

**Characteristics:**

- Server runs on YOUR machine
- Launched by your chatbot
- Communication via stdin/stdout (pipes)
- Fast (no network latency)
- No authentication needed
- Uses: `StdioServerParameters` + `stdio_client`

**Even though npx/uvx download code, they run it locally!**

```bash
# When you run:
npx -y @modelcontextprotocol/server-filesystem .

# What happens:
1. npx downloads package (if not cached)
2. Runs it locally: node_modules/.bin/server-filesystem .
3. Server starts on YOUR machine
4. Your chatbot talks via pipes
```

#### Remote Servers (Different!)

```
Your Machine              Remote Server
┌─────────────┐          ┌─────────────┐
│  Chatbot    │          │   Server    │
│             │  HTTP    │             │
│             ├─────────▶│             │
│             │  /SSE    │             │
│             │◀─────────┤             │
└─────────────┘          └─────────────┘
```

**Characteristics:**

- Server runs on another machine
- Already running (you don't launch it)
- Communication via HTTP/SSE
- Network latency
- Requires authentication
- Uses: `SSEServerParameters` + `sse_client`

**Example config:**

```json
{
  "remote-server": {
    "transport": "sse",
    "url": "https://my-server.example.com/mcp",
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

---

### The Open Ecosystem Model

#### Who Can Create MCP Servers?

**ANYONE!** This is the power of open protocols.

```
MCP Servers Can Come From:

1. Anthropic (reference implementations)
   └─ @modelcontextprotocol/server-*

2. Third-party developers
   └─ mcp-server-postgres
   └─ mcp-server-slack
   └─ mcp-server-docker

3. You! (after learning)
   └─ Your custom integrations
   └─ Share with community

4. Companies
   └─ Google → Gmail MCP server
   └─ GitHub → Enhanced GitHub server
   └─ Anyone wanting AI integration
```

#### Security Model

**Your server_config.json is like a script launcher:**

```json
{
  "mcpServers": {
    "trusted": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "my-code": {
      "command": "python",
      "args": ["/home/user/my_server.py"]
    },
    "third-party": {
      "command": "uvx",
      "args": ["unknown-package"]
    }
  }
}
```

**This runs arbitrary code on your machine!**

**Security Checklist:**

- ✅ Official Anthropic servers
- ✅ Well-known open source projects
- ✅ Your own code
- ⚠️ Third-party packages: Check source code
- ⚠️ Unknown packages: Verify publisher
- ❌ Random packages from untrusted sources

**Same security model as npm/pip:**

- Anyone can publish packages
- You choose what to run
- Trust is your responsibility

---

### The Protocol is the Contract

```
As long as a server speaks MCP correctly:

┌──────────────────────────────────────┐
│  MCP Protocol Requirements           │
├──────────────────────────────────────┤
│  1. JSON-RPC 2.0 messages            │
│  2. Standard method names            │
│     - initialize                     │
│     - tools/list                     │
│     - tools/call                     │
│     - resources/list                 │
│     - prompts/list                   │
│  3. Standard response formats        │
└──────────────────────────────────────┘

Your chatbot doesn't care about:
❌ What language server is written in
❌ Who created it
❌ What it does internally

Your chatbot only cares:
✅ Can I launch it?
✅ Does it speak JSON-RPC correctly?
✅ Does it follow MCP spec?
```

---

### Real-World Analogy: USB Ports

```
Computer (Chatbot)
    │
    │ USB Port (MCP Protocol)
    │
    ├─ Keyboard (filesystem server)
    ├─ Mouse (fetch server)
    ├─ Webcam (third-party server)
    └─ Flash Drive (your custom server)

USB doesn't care about:
- Device manufacturer
- Device brand
- Device purpose

USB only cares:
- Does it follow USB standard?
- Can it plug in and communicate?
```

---

## 💻 Code Structure & Explanation

### Complete Class Diagram

```
MCPChatbot
├── __init__()
│   ├─ sessions: Dict[str, ClientSession]
│   ├─ tool_to_session: Dict[str, str]
│   ├─ available_tools: List[Dict]
│   ├─ anthropic: Anthropic
│   └─ conversation_history: List[Dict]
│
├── load_server_config(config_path: str) → dict
│   └─ Loads server_config.json
│
├── connect_to_server(name: str, config: dict)
│   ├─ Creates StdioServerParameters
│   ├─ Launches subprocess via stdio_client
│   ├─ Stores session
│   └─ Calls discover_tools()
│
├── discover_tools(server_name: str, session: ClientSession)
│   ├─ Calls session.list_tools()
│   ├─ Populates tool_to_session mapping
│   └─ Populates available_tools list
│
├── setup()
│   ├─ Loads config
│   └─ Connects to all servers
│
├── execute_tool(tool_name: str, arguments: dict)  [TODO]
│   ├─ Looks up which server has the tool
│   └─ Executes tool on that server
│
└── chat()  [TODO]
    ├─ Gets user input
    ├─ Sends to Claude with available tools
    ├─ Handles tool calls
    └─ Returns responses
```

### Data Flow

```
1. Initialization
   MCPChatbot() → Empty dictionaries/lists

2. Setup Phase
   setup()
   ├─ load_server_config()
   │  └─ Returns: {"mcpServers": {...}}
   │
   ├─ connect_to_server("filesystem", {...})
   │  ├─ Launch: npx ...
   │  ├─ Store: sessions["filesystem"] = session
   │  └─ discover_tools()
   │     ├─ Query server for tools
   │     ├─ Map: tool_to_session["read_file"] = "filesystem"
   │     └─ Add: available_tools.append({...})
   │
   └─ connect_to_server("fetch", {...})
      └─ Same process...

3. Runtime (Chat Loop) [TO BE IMPLEMENTED]
   chat()
   ├─ User: "Read README.md"
   ├─ Claude API call with available_tools
   ├─ Claude response: Tool call "read_file"
   ├─ execute_tool("read_file", {"path": "README.md"})
   │  ├─ Lookup: tool_to_session["read_file"] = "filesystem"
   │  ├─ Get session: sessions["filesystem"]
   │  └─ Execute: session.call_tool("read_file", {...})
   └─ Return result to Claude
```

---

## ❓ Important Q&A Sessions

### Q1: Would it change much code if I use another LLM provider?

**Answer:** Yes, but only specific parts (~20-30% of code)

**What changes:**

- LLM API calls (Anthropic → OpenAI syntax)
- Response parsing (different formats)
- Authentication setup

**What stays the same:**

- All MCP client code
- Tool discovery logic
- Conversation loop structure

**Example:**

```python
# Anthropic
from anthropic import Anthropic
client = Anthropic(api_key="...")
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[...]
)

# OpenAI
from openai import OpenAI
client = OpenAI(api_key="...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...]
)
```

**Recommendation:** Start with Anthropic (course uses it), swap later once you understand the pattern.

---

### Q2: What is nest-asyncio and why do we need it?

**The Problem:**
Python normally doesn't allow nested event loops.

**JavaScript Comparison:**

```javascript
// This works fine in JavaScript
async function outer() {
  await inner()
}

async function inner() {
  await someAsyncOp()
}
```

**Python Without nest-asyncio:**

```python
# This might crash in some environments
async def outer():
    await inner()  # Error: event loop already running!

async def inner():
    await some_async_op()
```

**Python With nest-asyncio:**

```python
import nest_asyncio
nest_asyncio.apply()

# Now works everywhere!
async def outer():
    await inner()  # ✅ Works!
```

**When needed:**

- ✅ Jupyter notebooks
- ✅ Interactive environments
- ✅ Our MCP project (multiple async connections)
- ❌ Simple standalone scripts (optional)

**Think of it as:** Insurance that async code works in any environment.

---

### Q3: When do tool_to_session and available_tools get populated?

**Answer:** During the setup phase, after connecting to each server.

**Timeline:**

```
1. __init__() → Empty
2. setup() → Connects to servers
3. discover_tools() → Populates dictionaries
4. chat() → Uses populated data
```

**Detailed Flow:**

```python
# 1. Empty at start
self.tool_to_session = {}
self.available_tools = []

# 2. Connect to filesystem server
await connect_to_server("filesystem", config)
    # Launch npx subprocess
    # Store session
    await discover_tools("filesystem", session)
        # Server returns: [read_file, write_file, ...]
        # Populate:
        self.tool_to_session["read_file"] = "filesystem"
        self.tool_to_session["write_file"] = "filesystem"
        self.available_tools.append({
            "name": "read_file",
            "description": "...",
            "input_schema": {...}
        })

# 3. Connect to fetch server
await connect_to_server("fetch", config)
    # Same process...
    self.tool_to_session["fetch_url"] = "fetch"
    self.available_tools.append({...})

# 4. Now ready for chat!
# All mappings complete
```

---

### Q4: How does server_config.json relate to MCP standardization?

**Answer:** It's part of the MCP specification that enables the M+N solution.

**The Standard Structure:**

```json
{
  "mcpServers": {           // ← Standard key
    "server-id": {          // ← You choose name
      "command": "string",  // ← Standard field
      "args": ["array"],    // ← Standard field
      "env": {"object"}     // ← Optional standard field
    }
  }
}
```

**Why this matters:**

- Every MCP client knows this format
- Claude Desktop uses it
- Your chatbot uses it
- Any MCP app can read it

**Platform Independence:**

```json
// Node.js server
{"command": "npx", "args": ["-y", "package"]}

// Python server
{"command": "uvx", "args": ["package"]}

// Custom script
{"command": "python", "args": ["/path/to/script.py"]}

// Docker container
{"command": "docker", "args": ["run", "-i", "image"]}
```

**The Magic:**
MCP doesn't care HOW servers are launched, only that they speak the protocol!

---

### Q5: So servers can come from anyone, not just Anthropic?

**Answer:** YES! This is the power of open protocols.

**The Ecosystem:**

```
Anyone can create MCP servers:
├── Anthropic (reference)
├── Open source community
├── Companies (Google, Slack, etc.)
└── You!

As long as they follow the protocol:
├── JSON-RPC 2.0 messages
├── Standard method names
└── Correct response formats
```

**Real Example:**

```json
{
  "mcpServers": {
    "anthropic-filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "community-postgres": {
      "command": "npx",
      "args": ["-y", "mcp-server-postgres"]
    },
    "your-custom-server": {
      "command": "python",
      "args": ["/home/you/my_server.py"]
    }
  }
}
```

**Your chatbot:**

- Doesn't care who made the servers
- Only cares that they speak MCP
- Discovers and uses tools automatically

**This is why MCP is revolutionary!**

---

### Q6: Local vs Remote - How does stdio relate?

**Answer:** Our servers are LOCAL (subprocess), not remote.

**What Actually Happens:**

```bash
# Your config says:
"command": "npx",
"args": ["-y", "@modelcontextprotocol/server-filesystem", "."]

# When chatbot starts:
1. Downloads package (if needed)
2. Runs it locally as subprocess
3. Communicates via stdin/stdout pipes

# NOT:
❌ Connecting to remote server
❌ HTTP requests
❌ Network communication
```

**Visual:**

```
Your Machine
┌──────────────────────────┐
│  Chatbot (Python)        │
│    ↕ pipes (stdio)       │
│  Server (Node.js)        │
│  Both running locally!   │
└──────────────────────────┘
```

**Remote would be:**

```
Your Machine          Remote Server
┌───────────┐        ┌──────────┐
│  Chatbot  │ ----→  │  Server  │
│           │  HTTP  │          │
└───────────┘        └──────────┘
```

**Key Distinction:**

- `stdio_client` = Local subprocess
- `sse_client` = Remote HTTP server

---

## 🔒 Security Considerations

### What You're Actually Running

```json
{
  "mcpServers": {
    "server": {
      "command": "npx",
      "args": ["-y", "some-package"]
    }
  }
}
```

**This is equivalent to:**

```bash
npx -y some-package
```

**Which means:**

- Downloads code from npm/PyPI
- Runs it on YOUR machine
- With YOUR permissions
- Can access what you allow

### Trust Checklist

#### ✅ Trusted Sources

- Official Anthropic packages: `@modelcontextprotocol/server-*`
- Well-known open source (check GitHub stars, activity)
- Your own code
- Verified companies (official repos)

#### ⚠️ Verify First

- Third-party packages
  - Check source code
  - Read documentation
  - Look at GitHub issues
  - Check download counts

#### ❌ Avoid

- Random packages from unknown developers
- Packages with no source code
- Unverified publishers
- Packages with suspicious behavior

### Best Practices

1. **Review package source code** before adding to config
2. **Start with official servers** while learning
3. **Use virtual environments** to isolate packages
4. **Limit filesystem access** with specific paths
5. **Monitor what servers do** during development
6. **Keep packages updated** for security fixes

### The Filesystem Server Example

```json
{
  "filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "." // ← Only current directory!
    ]
  }
}
```

**This limits the server to current directory:**

- ✅ Can read/write in `mcp-chatbot-client/`
- ❌ Cannot access `/home/user/` or other folders
- 🛡️ Principle of least privilege

**Alternative:**

```json
"args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

Only allows access to `/tmp` folder.

---

## 🎯 What's Next

### Remaining Steps (To Be Completed)

#### Step 10: Execute Tool Calls

```python
async def execute_tool(self, tool_name: str, arguments: dict):
    """Execute a tool via its MCP server"""
    # Look up which server has this tool
    # Send tool call to that server
    # Return result
```

#### Step 11: The Chat Loop

```python
async def chat(self):
    """Main conversation loop"""
    # Get user input
    # Send to Claude with available_tools
    # Handle tool calls from Claude
    # Display responses
```

#### Step 12: Main Entry Point

```python
# main.py
async def main():
    bot = MCPChatbot()
    await bot.setup()
    await bot.chat()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 13: Testing

- Test with filesystem server
- Test with fetch server
- Test with multiple tool calls
- Test error handling

#### Step 14: Enhancements (Optional)

- Add logging
- Better error messages
- Save conversation history
- Add more servers from registry

### Course Progression

After completing this chatbot:

**Lesson 4-5:** Build your own MCP server

- Create custom tools
- Define resources
- Add prompt templates

**Lesson 7:** Add resources and prompts

- Beyond tools: data sources
- Prompt templates for common tasks

**Lesson 8:** Configure Claude Desktop

- Use your chatbot's servers in Claude Desktop
- See how official apps use MCP

**Lesson 9:** Deploy remote servers

- Convert local server to remote
- Deploy to cloud
- Add authentication

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "No module named 'anthropic'"

```bash
# Solution: Install dependencies
uv sync
```

#### 2. "ANTHROPIC_API_KEY not found"

```bash
# Solution: Check .env file exists and has key
cat .env
# Should show: ANTHROPIC_API_KEY=sk-...
```

#### 3. "npx: command not found"

```bash
# Solution: Install Node.js
# Ubuntu/Debian:
sudo apt install nodejs npm

# macOS:
brew install node

# Windows:
# Download from nodejs.org
```

#### 4. "Server connection timeout"

```bash
# Solution: Check if npx can run the server manually
npx -y @modelcontextprotocol/server-filesystem .

# Should start without errors
```

#### 5. "Event loop already running"

```python
# Solution: Make sure nest_asyncio is applied
import nest_asyncio
nest_asyncio.apply()

# Should be at top of file
```

### Debugging Tips

#### Check Server Config

```bash
cat server_config.json
# Validate JSON syntax
python -m json.tool server_config.json
```

#### Test MCP Server Manually

```bash
# Test filesystem server
npx -y @modelcontextprotocol/server-filesystem .

# Test fetch server
uvx mcp-server-fetch
```

#### Verify Environment

```bash
# Check Python version
python --version  # Should be 3.13

# Check Node.js
node --version  # Should be v22+

# Check uv
uv --version
```

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📚 Resources

### Official Documentation

- **MCP Documentation:** https://modelcontextprotocol.io/docs
- **MCP Specification:** https://spec.modelcontextprotocol.io
- **Anthropic API Docs:** https://docs.anthropic.com

### GitHub Repositories

- **MCP Python SDK:** https://github.com/modelcontextprotocol/python-sdk
- **Reference Servers:** https://github.com/modelcontextprotocol/servers
- **Server Registry:** https://github.com/modelcontextprotocol/registry

### Community

- **MCP Discussion Forum:** https://github.com/orgs/modelcontextprotocol/discussions
- **DeepLearning.AI Course:** https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic

---

## 📝 Quick Reference

### Key Files

```
mcp-chatbot-client/
├── .env                   # API keys (git-ignored!)
├── server_config.json     # MCP server config
├── chatbot.py            # Main chatbot class
└── main.py               # Entry point
```

### Key Commands

```bash
# Install dependencies
uv add package-name

# Run chatbot (when complete)
uv run python main.py

# Test server manually
npx -y @modelcontextprotocol/server-filesystem .
uvx mcp-server-fetch
```

### Key Concepts

- **MCP Host:** Your chatbot application
- **MCP Client:** Connection manager (one per server)
- **MCP Server:** Provides tools/resources/prompts
- **Session:** Active connection to a server
- **Tool:** Function Claude can call via MCP
- **stdio:** Standard input/output (local servers)
- **SSE:** Server-Sent Events (remote servers)

---

## 🎓 Learning Outcomes

### What You've Learned So Far

1. ✅ **MCP Fundamentals**

   - What MCP is and why it matters
   - M+N vs M×N problem
   - Client-server architecture

2. ✅ **Standardization**

   - How server_config.json enables interop
   - Protocol layers (discovery, transport, protocol)
   - Language-agnostic communication

3. ✅ **Local vs Remote**

   - Subprocess servers (stdio)
   - Remote servers (HTTP/SSE)
   - When to use each

4. ✅ **Open Ecosystem**

   - Anyone can create MCP servers
   - Trust and security model
   - Finding and using community servers

5. ✅ **Practical Implementation**
   - Project setup with uv
   - Dependency management
   - Environment configuration
   - Class structure
   - Async/await patterns

### What's Coming Next

6. ⏳ **Tool Execution**

   - Handling Claude's tool calls
   - Routing to correct server
   - Error handling

7. ⏳ **Conversation Loop**

   - User interaction
   - Claude integration
   - Response formatting

8. ⏳ **Testing & Debugging**
   - Real-world usage
   - Troubleshooting
   - Best practices

---

## 💡 Key Takeaways

### The Power of MCP

```
Before MCP:
- Custom integration for each AI app × tool combination
- Fragmented ecosystem
- Lots of duplicate work

With MCP:
- One client implementation per AI app
- One server implementation per tool
- Everything works together through standard protocol
```

### Your Chatbot as a Learning Tool

```
Your chatbot demonstrates:
1. How MCP clients discover servers
2. How tools are registered dynamically
3. How Claude uses MCP tools transparently
4. How the protocol enables interoperability
```

### The Bigger Picture

```
What you're building:
├── Today: MCP client connecting to existing servers
├── Tomorrow: Your own MCP servers
├── Future: Contributing to the ecosystem

The ecosystem grows when:
├── Developers create new servers
├── Companies adopt MCP
└── AI apps integrate MCP clients
```

---

**Last Updated:** Step 9 Complete (November 20, 2024)  
**Next Step:** Part 7 - Execute Tool Calls  
**Status:** Setup and discovery phase complete, chat loop pending

---

## 📖 Appendix: Async/Await Quick Reference

For those familiar with JavaScript:

### JavaScript

```javascript
async function fetchData() {
  const response = await fetch("https://api.example.com")
  const data = await response.json()
  return data
}

// Run it
fetchData().then((data) => console.log(data))
```

### Python

```python
async def fetch_data():
    response = await fetch('https://api.example.com')
    data = await response.json()
    return data

# Run it
import asyncio
asyncio.run(fetch_data())
```

### Key Similarities

- `async` keyword marks async functions
- `await` keyword waits for promises/coroutines
- Can chain multiple awaits
- Error handling with try/catch (JS) or try/except (Python)

### Key Differences

- Python requires `asyncio.run()` to start
- Python has explicit event loop management
- Python needs `nest_asyncio` for nested loops
- JavaScript has implicit event loop

---

_This guide will be updated as we complete remaining steps!_
