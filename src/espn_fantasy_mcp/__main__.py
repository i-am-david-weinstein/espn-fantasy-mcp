"""Entry point for ESPN Fantasy MCP server."""
import asyncio
import logging


def main():
    """Main entry point."""
    from espn_fantasy_mcp.server import main as server_main

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(server_main())


if __name__ == "__main__":
    main()
