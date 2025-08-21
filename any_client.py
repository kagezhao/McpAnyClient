#!/usr/bin/env python3
"""
any_client - A Python client for testing MCP servers

This tool allows users to connect to MCP servers using stdio, SSE or streamable HTTP,
list available tools, and call them with user-provided parameters.
"""

import argparse
import json
import asyncio
from datetime import timedelta
from typing import Dict, List, Any, Optional, Union

import logging
from fastmcp import Client
from fastmcp.mcp_config import RemoteMCPServer
from mcp.types import CallToolResult


class FastMcpClient:
    def __init__(self, server_url: str, transport_type: str = "sse", headers: dict[str, str] = {}):
        self.server_url = server_url
        self.headers = headers
        
        # https://gofastmcp.com/clients/transports#mcp-json-configuration-transport
        if transport_type == "stdio":
            parts = server_url.strip().split(" ", 1)
            command = parts[0]
            args = parts[1].split() if len(parts) > 1 else []
            config = {
                "mcpServers": {
                    "server1": {
                        "command": command,
                        "args": args,
                        "env": headers,
                    }
                }
            }
            print(f"\nstarting stdio mcp with config:\n{config}\n")
        else:
            # see fastmcp.mcp_config 中 RemoteMCPServer
            config = {
                "mcpServers": {
                    "server1": {
                        "url": self.server_url,
                        "headers": headers,
                        "transport": transport_type,
                        "sse_read_timeout": timedelta(seconds=3600),
                    }
                }
            }

        self.client = Client(config)

    async def connect_and_loop(self):
        async with self.client:
            self.tools = await self.client.list_tools()
            self.cmd_list_tools()
            await self.cmd_loop()
            
    async def cmd_dump_tools_schema(self):
        tools_schema = [tool.model_dump() for tool in self.tools]
        s = json.dumps(tools_schema, indent=2, ensure_ascii=False)
        with open("schema.json", "w", encoding="utf-8") as f:
            f.write(s)
        print("schema.json saved")

    async def cmd_show_tool_schema(self, index: int) -> str:
        if index < 0 or index >= len(self.tools):
            return None
        
        tool_schema = self.tools[index].model_dump()
        s = json.dumps(tool_schema, indent=2, ensure_ascii=False)
        print(s)
        return tool_schema['name']

    def cmd_list_tools(self):
        print("==================================")
        print(f"index | tool name")
        for i, tool in enumerate(self.tools, 1):
            print(f" {i:<4} | {tool.name}")
        print("==================================")
            
    async def log_callback(self, progress: float, total: float | None, message: str | None):
        print(f"[PROGRESS] {progress}/{total} {message}\n")
        return

    async def cmd_call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None):
        print(f"call tool {tool_name} ...")
        try:
            result = await self.client.call_tool(tool_name, arguments or {}, progress_handler=self.log_callback)
            self.pretty_print_tool_result(result)

        except Exception as e:
            print(f"Failed to call tool '{tool_name}': {e}")

    def pretty_print_tool_result(self, result: CallToolResult):
        print("\n================ tool result ===============\n")
        if hasattr(result, "content"):
            for content in result.content:
                if content.type == "text":
                    try:
                        # 如果是json格式则友好输出
                        json_data = json.loads(content.text)
                        print(json.dumps(json_data, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print(content.text)
                else:
                    print(content)
        else:
            print(result)
            
    def input_json(self, prompt: str) -> Any:
        """像 input(prompt).strip()，但支持多行输入直到合法 JSON，返回解析后的对象"""
        lines = ""
        while True:
            line = input(prompt if not lines else "")
            lines += line
            lines = lines.strip()
            
            if not lines.startswith("{"):
                # 已经不可能成功了，直接提示，并重来
                print("invalid json format")
                lines = ""
                continue
            
            try:
                return json.loads(lines)
            except json.JSONDecodeError:
                continue
            
    async def cmd_loop(self):
        prompt = "输入工具编号，或者list/dump/quit >"

        while True:

            command = input(prompt).strip()

            if not command:
                continue

            elif command == "list":
                await self.cmd_list_tools()
            elif command == "dump":
                await self.cmd_dump_tools_schema()
            elif command == "quit":
                break
            elif command.isdigit():
                tool_name = await self.cmd_show_tool_schema(int(command)-1)
                if tool_name:
                    arguments = self.input_json(f"\n\ninput call tool {tool_name} json args (support multiple lines json) :\n")
                    await self.cmd_call_tool(tool_name, arguments)
            else:
                print("Unknown command")


SAMPLE = """
sample:
any_client.py -type sse -url http://your.com/sse
any_client.py -type http -url http://your.com/mcp
any_client.py -type stdio -url "npx -y @modelcontextprotocol/server-sequential-thinking"
"""

async def main():
    parser = argparse.ArgumentParser(description="MCP testing tool")
    parser.add_argument("-url", help="sse/streamable: URL. stdio: command line; see sample.", default="")
    parser.add_argument("-type", help="mcp type (sse/http/stdio), http=streamable http", default="")
    parser.add_argument("-debug", help="mcp debug log", action="store_true")
    parser.add_argument("-header", help="HTTP header. sample --> McpSession: abc123", action="append", default=[])
    
    args = parser.parse_args()
    
    url = args.url
    mcp_type = args.type
    
    # Prompt for input URL if not provided
    if not url:
        parser.print_help()
        print(SAMPLE)
        
        print(f"\n\ninput url (sse or streamable):")
        url = input().strip()
        
        if not url.startswith("http"):
            print("URL string must start with http")
            await asyncio.sleep(1)
            return
    
    if not mcp_type:
        # guess from url
        if "sse" in url:
            mcp_type = "sse"
        else:
            mcp_type = "http"
        
    
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
    
    # Parse headers
    headers = {}
    for header in args.header:
        parts = header.split(":", 1)
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip()
            print(f"Use Header {key}:{val}")
            headers[key] = val
        else:
            print(f"Invalid header format: {header}")
    
    client = FastMcpClient(url, mcp_type, headers)
    await client.connect_and_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
    except EOFError:
        print()
