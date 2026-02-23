from src.mcp_server.server import MCPServer
import asyncio

async def main():
    server_config = MCPServer(
        server_name="pg_ai",
        instructions="MCP Server to handle database operations"
    )
    mcp_server = server_config.get_mcp_server()
    await mcp_server.run_async(
        transport="streamable-http"
    )

if __name__ == "__main__":
    asyncio.run(main())

