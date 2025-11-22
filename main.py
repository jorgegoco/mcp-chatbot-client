import asyncio
from chatbot import MCPChatbot


async def main():
    """Main entry point for the MCP chatbot"""
    chatbot = MCPChatbot()
    await chatbot.connect_to_servers_and_run()


if __name__ == "__main__":
    asyncio.run(main())