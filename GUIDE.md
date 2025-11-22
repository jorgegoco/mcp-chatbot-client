# MCP Chatbot Client - Personal Learning Guide

> **My Journey:** Building an MCP-compatible chatbot client from scratch  
> **Date:** November 20-22, 2024  
> **Status:** ✅ Complete & Production-Ready

---

## 📋 Table of Contents

1. [Quick Reference](#quick-reference)
2. [What I Built](#what-i-built)
3. [Step-by-Step Journey](#step-by-step-journey)
4. [Key Concepts Learned](#key-concepts-learned)
5. [Code Evolution](#code-evolution)
6. [Problems Solved](#problems-solved)
7. [Important Q&A](#important-qa)
8. [Configuration Guide](#configuration-guide)
9. [Cost Optimization](#cost-optimization)
10. [Future Enhancements](#future-enhancements)

---

## 🎯 Quick Reference

### Running the Chatbot

```bash
uv run python main.py
```

### Project Structure

```
mcp-chatbot-client/
├── .env                    # ANTHROPIC_API_KEY=your_key_here
├── .gitignore             # Must include .env!
├── server_config.json     # MCP server configuration
├── chatbot.py            # Main chatbot implementation
├── main.py               # Entry point
└── pyproject.toml        # Dependencies
```

### Key Commands

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Test servers manually
npx -y @modelcontextprotocol/server-filesystem .
uvx --quiet mcp-server-fetch
```

---

## 🏗️ What I Built

### Core Features

- ✅ **Multi-server MCP client** - Connects to unlimited external MCP servers
- ✅ **Dynamic tool discovery** - Automatically finds and registers tools
- ✅ **Claude AI integration** - Powered by Anthropic's API
- ✅ **Scalable architecture** - AsyncExitStack for managing any number of servers
- ✅ **Interactive chat interface** - User-friendly conversation loop
- ✅ **Robust error handling** - Individual server failures don't crash the app

### Current Capabilities

```
Available Tools:
├─ filesystem server
│  ├─ read_file - Read file contents
│  ├─ write_file - Create/overwrite files
│  └─ list_directory - List directory contents
└─ fetch server
   └─ fetch - Fetch web content as markdown
```

---

## 📚 Step-by-Step Journey

### Step 1: Project Setup

**Decision:** Named it `mcp-chatbot-client` (clear, descriptive)

**Actions:**

```bash
uv init
uv add anthropic mcp python-dotenv nest-asyncio
touch .env server_config.json
echo ".env" >> .gitignore  # CRITICAL for security!
```

**Why these dependencies:**

- `anthropic` - Claude API client
- `mcp` - Model Context Protocol SDK
- `python-dotenv` - Secure API key management
- `nest-asyncio` - Nested async support (for MCP's multiple connections)

---

### Step 2: Understanding MCP

**The Problem MCP Solves:**

```
Before MCP:
5 AI Apps × 10 Tools = 50 custom integrations 😱

With MCP:
5 AI Apps + 10 Tools = 15 integrations 🎉
```

**Core Architecture:**

```
Your Chatbot (MCP Host)
    ├─ MCP Client 1 → MCP Server 1 (filesystem)
    ├─ MCP Client 2 → MCP Server 2 (fetch)
    └─ MCP Client N → MCP Server N (any!)
```

**Key Insight:** MCP is like USB for AI - standardized protocol, plug-and-play tools!

---

### Step 3: Server Configuration

Created `server_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "fetch": {
      "command": "uvx",
      "args": ["--quiet", "mcp-server-fetch"]
    }
  }
}
```

**Important learnings:**

- Servers run as local subprocesses (not remote!)
- `command` + `args` = shell command to launch server
- `.` in filesystem = only current directory (security!)
- `--quiet` flag = suppress npm noise

---

### Step 4: Initial Implementation (Nested Approach)

**First attempt:** Nested `async with` blocks

```python
async with server1:
    async with server2:
        await chat_loop()
```

**Problem identified:** Doesn't scale! Each server adds nesting depth.

---

### Step 5: Scalable Refactoring

**Solution:** AsyncExitStack pattern

```python
async with AsyncExitStack() as stack:
    for server in servers:
        # Add contexts dynamically
        await stack.enter_async_context(...)
    await chat_loop()  # All connections alive!
```

**Why this is better:**

- Works with unlimited servers
- Constant nesting depth (always 2 levels)
- Individual error handling
- Production-ready pattern

---

### Step 6: Tool Execution

**How it works:**

1. User asks Claude to do something
2. Claude decides which tool to use
3. Chatbot looks up which server has that tool
4. Executes tool via MCP session
5. Returns result to Claude
6. Claude provides final response

**Code flow:**

```python
tool_name = "read_file"
server_name = self.tool_to_session[tool_name]  # → "filesystem"
session = self.sessions[server_name]
result = await session.call_tool(tool_name, arguments)
```

---

### Step 7: Chat Loop Implementation

**Features:**

- Interactive input/output
- Special commands (`tools`, `quit`)
- Multi-turn conversations
- Tool call handling
- Error recovery

**User experience:**

```
You: Read README.md
🔧 Calling tool 'read_file' with args: {'path': 'README.md'}
✅ Tool executed

Claude: I've read your README. It contains...
```

---

### Step 8: Problem Solving

**Issue 1: npm noise in fetch server**

```
Failed to parse JSONRPC message from server
Error: "added 48 packages, and audited 49 packages in 4s"
```

**Solution:** Add `--quiet` flag to uvx command

```json
"args": ["--quiet", "mcp-server-fetch"]
```

**Issue 2: Scalability concerns**

- Nested contexts don't scale
- Refactored to AsyncExitStack
- Now supports unlimited servers

---

## 🧠 Key Concepts Learned

### 1. MCP is Open & Decentralized

**Anyone can create MCP servers:**

- Anthropic (official reference servers)
- Open source community
- Companies (Google, Slack, etc.)
- Me! (future project)

**As long as they speak the protocol:**

- JSON-RPC 2.0 messages
- Standard method names (`tools/list`, `tools/call`)
- Correct response formats

---

### 2. Local vs Remote Servers

**Local (what we use):**

```
Your Machine
├─ Chatbot (Python)
├─ Filesystem Server (Node.js subprocess)
└─ Fetch Server (Python subprocess)
Communication: stdio (stdin/stdout pipes)
```

**Remote (future):**

```
Your Machine          Cloud Server
├─ Chatbot    ─HTTP─→  MCP Server
Communication: HTTP/SSE
```

**Key difference:**

- `stdio_client` = Local subprocess
- `sse_client` = Remote HTTP server

---

### 3. AsyncExitStack Pattern

**Problem:** Can't nest `async with` dynamically in a loop

**Old (doesn't work in loop):**

```python
async with resource() as r:
    use(r)
```

**New (works in loop):**

```python
async with AsyncExitStack() as stack:
    for item in items:
        r = await stack.enter_async_context(resource())
        use(r)
```

**Real-world benefit:** Add unlimited servers without code changes!

---

### 4. MCP Communication Flow

```
1. Initialize
   Client → Server: "initialize"
   Server → Client: capabilities

2. List Tools
   Client → Server: "tools/list"
   Server → Client: [tool1, tool2, tool3]

3. Call Tool
   Client → Server: "tools/call" + tool_name + arguments
   Server → Client: result

4. Multiple Calls
   Repeat step 3 as many times as needed
```

---

### 5. Tool Discovery & Mapping

**How the chatbot knows which server has which tool:**

```python
# During setup, for each server:
tools = await session.list_tools()

for tool in tools:
    # Map tool → server
    self.tool_to_session[tool.name] = server_name

    # Store tool definition for Claude
    self.available_tools.append({
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    })
```

**Result:**

```python
self.tool_to_session = {
    "read_file": "filesystem",
    "write_file": "filesystem",
    "list_directory": "filesystem",
    "fetch": "fetch"
}
```

---

## 💻 Code Evolution

### Version 1: Hardcoded Nested Contexts

```python
async def connect_to_servers_and_run(self):
    # Only works for exactly 2 servers
    async with server1_context:
        async with server2_context:
            await chat_loop()
```

**Problems:**

- ❌ Hardcoded for 2 servers
- ❌ Deep nesting (4 levels)
- ❌ Not scalable
- ❌ Poor error handling

---

### Version 2: AsyncExitStack (Current)

```python
async def connect_to_servers_and_run(self):
    async with AsyncExitStack() as stack:
        # Works for any number of servers
        for server_name, config in servers.items():
            try:
                # Add context to stack
                read, write = await stack.enter_async_context(
                    stdio_client(params)
                )
                session = await stack.enter_async_context(
                    ClientSession(read, write)
                )
                # Setup this server...
            except Exception:
                # Skip failed servers
                continue

        # All servers connected
        await chat_loop()
```

**Benefits:**

- ✅ Works with unlimited servers
- ✅ Constant nesting (2 levels always)
- ✅ Scalable via config only
- ✅ Individual error handling

---

### Key Code Changes

**1. Added import:**

```python
from contextlib import AsyncExitStack
```

**2. Changed connection pattern:**

```python
# OLD:
async with stdio_client(...) as (read, write):

# NEW:
read, write = await stack.enter_async_context(stdio_client(...))
```

**3. Added error handling:**

```python
for server in servers:
    try:
        # Connect
    except Exception:
        continue  # Don't crash, skip this server
```

---

## 🔧 Problems Solved

### Problem 1: API Key Security

**Issue:** API key could be committed to Git

**Solution:**

```bash
# Create .env
echo "ANTHROPIC_API_KEY=your_key" > .env

# Add to .gitignore
echo ".env" >> .gitignore

# Verify
git status  # .env should NOT appear
```

---

### Problem 2: npm Noise Pollution

**Issue:** npm messages in JSON-RPC stream

```
Failed to parse JSONRPC message: "added 48 packages..."
```

**Solution:** Add `--quiet` flag

```json
"args": ["--quiet", "mcp-server-fetch"]
```

---

### Problem 3: Scalability Limitations

**Issue:** Nested contexts don't scale

```python
# For 5 servers:
async with s1:
    async with s2:
        async with s3:
            async with s4:
                async with s5:
                    # 10 levels deep! 😱
```

**Solution:** AsyncExitStack

```python
# For any number of servers:
async with AsyncExitStack() as stack:
    for server in servers:
        await stack.enter_async_context(...)
    # Always 2 levels! ✅
```

---

### Problem 4: Error Handling

**Issue:** One server failure crashes everything

**Solution:** Individual try-except per server

```python
for server in servers:
    try:
        connect_to_server()
    except Exception:
        print(f"Failed: {server}")
        continue  # Keep going with other servers
```

---

## ❓ Important Q&A

### Q: Would it change much code to use another LLM provider?

**A:** Only ~20-30% of code (the Claude API calls)

**What changes:**

- API client initialization
- Message format
- Response parsing

**What stays the same:**

- All MCP code
- Tool discovery
- Chat loop structure

**Example:**

```python
# Anthropic
response = anthropic.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[...]
)

# OpenAI (if switching)
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[...]
)
```

---

### Q: What is nest-asyncio and why do we need it?

**A:** It allows nested event loops

**Problem:** Python normally doesn't allow:

```python
async def outer():
    await inner()  # Error if loop already running!
```

**Solution:** `nest_asyncio.apply()`

**When needed:**

- ✅ Jupyter notebooks
- ✅ Interactive environments
- ✅ Multiple async MCP connections
- ❌ Simple standalone scripts (optional)

---

### Q: Can servers come from anyone, not just Anthropic?

**A:** YES! That's the power of open protocols.

**MCP ecosystem:**

- Anthropic's reference servers
- Community servers (postgres, slack, docker...)
- Your custom servers
- Company integrations

**As long as they:**

- Speak JSON-RPC 2.0
- Follow MCP spec
- Implement standard methods

---

### Q: How does server_config.json enable standardization?

**A:** It's part of the MCP spec!

**Same format everywhere:**

```json
{
  "mcpServers": {
    // ← Standard key
    "server-name": {
      "command": "string", // ← Standard field
      "args": ["array"] // ← Standard field
    }
  }
}
```

**Result:** This works with:

- Your Python chatbot
- Claude Desktop
- Cursor IDE
- Any MCP-compatible app

---

## ⚙️ Configuration Guide

### Server Configuration Format

```json
{
  "mcpServers": {
    "server-id": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {
        "OPTIONAL_VAR": "value"
      }
    }
  }
}
```

### Examples

**Python server:**

```json
{
  "my-server": {
    "command": "uv",
    "args": ["run", "my_server.py"]
  }
}
```

**Node.js server:**

```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "your_token"
    }
  }
}
```

**Docker container:**

```json
{
  "containerized": {
    "command": "docker",
    "args": ["run", "-i", "my-mcp-server:latest"]
  }
}
```

---

## 💰 Cost Optimization

### Claude Model Comparison

| Model          | Input    | Output   | Speed   | Use Case              |
| -------------- | -------- | -------- | ------- | --------------------- |
| **Haiku 4.5**  | $1/MTok  | $5/MTok  | ⚡ Fast | Testing (recommended) |
| **Sonnet 4.5** | $3/MTok  | $15/MTok | 🚀 Med  | Production            |
| **Opus 4**     | $15/MTok | $75/MTok | 🐢 Slow | Premium               |

### Switching Models

In `chatbot.py`, change TWO locations:

```python
# Line ~72 and ~110
model='claude-haiku-4-5-20251001'  # Instead of sonnet
```

### Cost Comparison

**1000 queries with Haiku:** ~$10-15  
**1000 queries with Sonnet:** ~$30-45  
**Savings:** 67% cheaper!

---

## 🚀 Future Enhancements

### Level 1: Add More Servers

```json
{
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": { "BRAVE_API_KEY": "your_key" }
  },
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": { "GITHUB_TOKEN": "your_token" }
  }
}
```

---

### Level 2: Build Custom Server

Follow course Lessons 4-5:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-custom-server")

@mcp.tool()
def my_tool(arg: str) -> str:
    """Your custom functionality"""
    return f"Processed: {arg}"

if __name__ == "__main__":
    mcp.run()
```

---

### Level 3: Add Features

**Conversation history:**

```python
def save_conversation(self):
    with open('history.json', 'w') as f:
        json.dump(self.conversation_history, f)
```

**Logging:**

```python
import logging
logging.basicConfig(
    filename='chatbot.log',
    level=logging.INFO
)
```

**Streaming responses:**

```python
response = anthropic.messages.stream(...)
for event in response:
    print(event.content, end='', flush=True)
```

---

### Level 4: Deploy Remote Server

Follow course Lesson 9:

```json
{
  "remote": {
    "transport": "sse",
    "url": "https://my-server.com/sse",
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

---

## 🎯 Testing Scenarios

### Basic Tests

```
1. View tools:
   You: tools

2. Read file:
   You: Read the README.md file

3. Write file:
   You: Create a file called test.txt with "Hello MCP!"

4. List directory:
   You: List all files in this directory

5. Fetch web:
   You: Fetch https://www.anthropic.com and summarize
```

### Advanced Tests

```
6. Multiple tools:
   You: List files, then create summary.txt with the list

7. Complex query:
   You: Read all .py files and create a project_overview.txt

8. Web research:
   You: Fetch 3 articles about MCP and compare them
```

---

## 📊 Project Metrics

**Development time:** ~8 hours (with learning)  
**Lines of code:** ~200 (chatbot.py + main.py)  
**Dependencies:** 4 core packages  
**MCP servers:** 2 (scalable to unlimited)  
**Available tools:** 4 tools discovered automatically

---

## 🎓 Key Takeaways

### What I Learned

1. **MCP fundamentals** - Protocol, architecture, ecosystem
2. **Async patterns** - AsyncExitStack, context managers
3. **Problem-solving** - Scalability, security, error handling
4. **Production thinking** - Clean code, documentation, testing

### Skills Demonstrated

- ✅ Python async/await
- ✅ MCP protocol
- ✅ API integration
- ✅ Error handling
- ✅ Security best practices
- ✅ Documentation
- ✅ Scalable architecture

---

## 📚 Resources

### Official Docs

- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [MCP Specification](https://spec.modelcontextprotocol.io)
- [Anthropic API](https://docs.anthropic.com)

### GitHub

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Reference Servers](https://github.com/modelcontextprotocol/servers)
- [Server Registry](https://github.com/modelcontextprotocol/registry)

### Course

- [DeepLearning.AI MCP Course](https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic)

---

## 🎊 Achievement Unlocked!

✅ Built complete MCP chatbot client  
✅ Learned Model Context Protocol  
✅ Mastered Python async patterns  
✅ Created production-ready code  
✅ Documented the journey

**Ready for:** Building custom MCP servers, contributing to ecosystem, production deployments!

---

**Last Updated:** November 22, 2024  
**Status:** Complete & Working  
**Next:** Lessons 4-9 of DeepLearning.AI course
