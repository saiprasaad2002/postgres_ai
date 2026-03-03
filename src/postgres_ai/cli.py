import asyncio
import typer
from typing import Optional
from postgres_ai.loaders.env_loader import get_mcp_settings
from postgres_ai.mcp_server.server import PgMCP
from postgres_ai.connectors.pg_connector import PGConnector
from postgres_ai.logger.mcp_logger import get_mcp_logger
from fastmcp.server.lifespan import lifespan


app = typer.Typer(
    name="postgres_ai",
    help="Postgres AI MCP Server — run AI tools directly on your database",
    add_completion=True,
    no_args_is_help=True,
)

@app.command()
def main(
    env_file: Optional[str] = typer.Option(".env", "--env-file", "-e", help="Path to .env file"),
    host: str = typer.Option("0.0.0.0", "--host", help="MCP server host"),
    port: int = typer.Option(8000, "--port", "-p", help="MCP server port"),
    transport: str = typer.Option("streamable-http", "--transport"),
    db_host: Optional[str] = typer.Option(None, "--db-host", envvar="DB_HOST"),
    db_port: Optional[int] = typer.Option(None, "--db-port", envvar="DB_PORT"),
    db_user: Optional[str] = typer.Option(None, "--db-user", envvar="DB_USER"),
    db_name: Optional[str] = typer.Option(None, "--db-name", envvar="DB_NAME"),
    prompt_password: bool = typer.Option(
        False, "--prompt-password", help="Interactively ask for DB password (overrides .env)"
    ),
):
    """Start the postgres_ai MCP Server"""
    print("🚀 Welcome to postgres_ai MCP Server!")

    try:
        settings = get_mcp_settings(env_file)
    except Exception as e:
        typer.secho(f"❌ Config error: {e}", fg=typer.colors.RED)
        typer.secho("Tip: Copy .env.example → .env and fill the values", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    # Apply CLI overrides
    db_host = db_host or settings.db_host
    db_port = db_port or settings.db_port
    db_user = db_user or settings.db_user
    db_name = db_name or settings.db_name

    # Password handling
    if prompt_password or not getattr(settings, "db_pass", None):
        db_pass = typer.prompt("Database Password", hide_input=True, confirmation_prompt=True)
    else:
        db_pass = settings.db_pass

    logger = get_mcp_logger()

    conn = PGConnector(
        db_user=db_user,
        db_host=db_host,
        db_port=db_port,
        db_pass=db_pass,
        db_name=db_name,
    )

    @lifespan
    async def mcp_lifespan(server):
        try:
            database = await conn.connect()
            logger.info(f"✅ Connected to Postgres @ {db_host}:{db_port}")
            yield {"pg_connection": database, "logger": logger}
        finally:
            await conn.disconnect()
            logger.info("Database connection closed")

    server_config = PgMCP(
        lifespan=mcp_lifespan,
        server_name="postgres_ai",
        instructions="MCP Server to handle Postgres database operations with AI tools",
    )
    mcp_server = server_config.get_mcp_server()

    typer.secho(f"Connected with Database @ {db_host}:{db_port}", fg=typer.colors.GREEN)
    typer.secho(f"MCP Server starting @ {host}:{port}", fg=typer.colors.GREEN)
    asyncio.run(
        mcp_server.run_async(transport=transport, host=host, port=port)
    )


if __name__ == "__main__":
    app()