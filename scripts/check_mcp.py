from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("KERYX_MCP_URL", "http://127.0.0.1:8001/mcp")
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print([tool.name for tool in (await session.list_tools()).tools])


if __name__ == "__main__":
    asyncio.run(main())
