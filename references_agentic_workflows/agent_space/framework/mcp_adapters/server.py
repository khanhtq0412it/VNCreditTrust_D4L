import asyncio
from typing import Any, Dict, List, Optional, Union
import inspect
from variables.helper import ConfigLoader
from variables.mcp import MCPConfig
from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPClientWrapper:
    """
    High-level wrapper around MultiServerMCPClient for interacting with
    dynamically loaded MCP servers based on configuration variables.

    This wrapper sanitizes schemas returned by MCP servers to remove
    `additionalProperties` keys from plain Python dict/list structures.
    """

    def __init__(self) -> None:
        raw_config = ConfigLoader.load_single(MCPConfig)
        self.server_map = self._discover_servers(raw_config)
        self.client = MultiServerMCPClient(self.server_map)

    # ------------------------------------------------------------------
    def _discover_servers(self, config: Dict[str, Optional[str]]) -> Dict[str, Dict[str, str]]:
        """
        Build the server map from configuration variables, ignoring entries
        whose URL value is None or empty. This prevents runtime errors when
        libraries expect a string URL.
        """
        server_map: Dict[str, Dict[str, str]] = {}

        for key, value in config.items():
            if key.startswith("MCP_SERVER_") and key.endswith("_URL"):
                name = (
                    key.replace("MCP_SERVER_", "")
                       .replace("_URL", "")
                       .lower()
                )
                # Skip entries that are None or empty strings
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    # don't include servers without an URL
                    # keep behavior explicit: skip silently (but could log)
                    continue

                server_map[f"{name}-server"] = {
                    "transport": "streamable_http",
                    "url": value
                }

        if not server_map:
            raise RuntimeError("No MCP server URLs found in configuration.")
        return server_map

    # ------------------------------------------------------------------
    # --- helper: sanitize returned structures ---
    def _remove_additional_properties(self, obj: Any) -> Any:
        """Recursively remove 'additionalProperties' keys from dicts/lists.

        Only operates on plain Python dict/list structures. Other object types
        (proto messages, class instances, etc.) are returned unchanged so we
        don't accidentally mutate library types.
        """
        if isinstance(obj, dict):
            cleaned: Dict[Any, Any] = {}
            for k, v in obj.items():
                if k == "additionalProperties":
                    # drop this key
                    continue
                cleaned[k] = self._remove_additional_properties(v)
            return cleaned
        if isinstance(obj, list):
            return [self._remove_additional_properties(v) for v in obj]
        return obj

    def _matches_tool_name(self, tool: Any, name: str) -> bool:
        """Return True if the given tool (dict or object) matches the name."""
        if isinstance(tool, dict):
            return (tool.get("name") == name) or (tool.get("title") == name)
        return getattr(tool, "name", None) == name

    # NOTE: The dedicated `aget_tool` helper was removed. All searching
    # functionality is implemented in `aget_tools` below; use that for
    # single-tool and multi-tool queries.

    async def aget_tools(
        self,
        server_name: Optional[Union[str, List[str]]] = None,
        tool_name: Optional[Union[str, List[str]]] = None,
    ) -> Any:
        """Flexible async tool retrieval.

        Supported call patterns:
        - aget_tools() -> returns list of tools from all servers.
        - aget_tools(server_name="s") -> list of tools for server 's'.
        - aget_tools(server_name=["s1","s2"]) -> aggregate list of tools from those servers.
        - aget_tools(server_name="s", tool_name="t") -> return single tool 't' from server 's' or raise ValueError.
        - aget_tools(server_name="s", tool_name=["t1","t2"]) -> return list of tools found on server 's' or raise ValueError for missing.
        - aget_tools(server_name=["s1","s2"], tool_name="t") -> return all matches of 't' across the servers list or raise ValueError if none found.
        - aget_tools(server_name=["s1","s2"], tool_name=["t1","t2"]) -> return flattened list of matches for each requested tool across the servers list; raise ValueError for any missing tool.

        Note: calling with tool_name but without server_name is invalid and will raise
        ValueError: caller must specify server scope when requesting specific tool(s).
        """
        # Invalid: tool_name without server_name
        if tool_name and not server_name:
            raise ValueError("When requesting a specific tool (tool_name), you must also provide server_name")

        server_is_list = isinstance(server_name, list)

        # Case 1: No args -> all tools across all servers
        if server_name is None and tool_name is None:
            tools = await self.client.get_tools()
            try:
                return [self._remove_additional_properties(t) if isinstance(t, (dict, list)) else t for t in tools]
            except Exception:
                return tools

        # Case 2: server_name is list, no tool_name -> aggregate tools from list
        elif server_is_list and tool_name is None:
            combined: List[Any] = []
            for s in server_name:  # type: ignore[arg-type]
                self._validate_server_name(s)
                try:
                    tools = await self.client.get_tools(server_name=s)
                except Exception:
                    continue
                for t in tools:
                    combined.append(self._remove_additional_properties(t) if isinstance(t, (dict, list)) else t)
            return combined

        # Case 3: server_name is list, tool_name provided -> search requested tool(s) across the provided servers
        elif server_is_list and tool_name is not None:
            requested_names = [tool_name] if isinstance(tool_name, str) else list(tool_name)  # type: ignore[arg-type]
            found_map: Dict[str, List[Any]] = {name: [] for name in requested_names}
            for s in server_name:  # type: ignore[arg-type]
                self._validate_server_name(s)
                try:
                    tools = await self.client.get_tools(server_name=s)
                except Exception:
                    continue
                for t in tools:
                    for name in requested_names:
                        if self._matches_tool_name(t, name):
                            found_map[name].append(self._remove_additional_properties(t) if isinstance(t, (dict, list)) else t)
            # single tool_name -> return matches list or raise
            if isinstance(tool_name, str):
                matches = found_map.get(tool_name, [])
                if not matches:
                    raise ValueError(f"Tool '{tool_name}' not found on any of servers {server_name}")
                return matches
            # tool_name list -> ensure each requested name has matches
            missing = [n for n, v in found_map.items() if not v]
            if missing:
                raise ValueError(f"Tools not found on servers {server_name}: {missing}")
            results: List[Any] = []
            for n in requested_names:
                results.extend(found_map[n])
            return results

        # Case 4: server_name is single string, no tool_name -> full list for server
        elif isinstance(server_name, str) and tool_name is None:
            self._validate_server_name(server_name)
            tools = await self.client.get_tools(server_name=server_name)
            try:
                return [self._remove_additional_properties(t) if isinstance(t, (dict, list)) else t for t in tools]
            except Exception:
                return tools

        # Case 5: server_name is string and tool_name provided
        elif isinstance(server_name, str) and tool_name is not None:
            self._validate_server_name(server_name)
            tools = await self.client.get_tools(server_name=server_name)
            # single tool requested
            if isinstance(tool_name, str):
                for t in tools:
                    if self._matches_tool_name(t, tool_name):
                        return self._remove_additional_properties(t) if isinstance(t, (dict, list)) else t
                raise ValueError(f"Tool '{tool_name}' not found on server '{server_name}'")
            # list of tools requested
            if isinstance(tool_name, list):
                found: List[Any] = []
                missing: List[str] = []
                for name in tool_name:
                    matched = None
                    for t in tools:
                        if self._matches_tool_name(t, name):
                            matched = self._remove_additional_properties(t) if isinstance(t, (dict, list)) else t
                            break
                    if matched is None:
                        missing.append(name)
                    else:
                        found.append(matched)
                if missing:
                    raise ValueError(f"Tools not found on server '{server_name}': {missing}")
                return found

        # Should not reach here
        else:
            raise ValueError("Unsupported combination of server_name and tool_name")

    # ASYNC API (official)

    async def aget_resources(self, server_name: str) -> List[Any]:
        self._validate_server_name(server_name)
        return await self.client.get_resources(server_name=server_name)

    async def aget_prompts(self, server_name: str, prompt_name: str) -> List[Any]:
        self._validate_server_name(server_name)
        return await self.client.get_prompt(
            server_name=server_name,
            prompt_name=prompt_name
        )

    # ------------------------------------------------------------------
    # SYNC wrappers (terminal-safe, not recommended for notebook)

    def get_tools(
        self,
        server_name: Optional[Union[str, List[str]]] = None,
        tool_name: Optional[Union[str, List[str]]] = None,
    ) -> Any:
        """Synchronous wrapper to retrieve tools.

        server_name and tool_name may each be a string or a list of strings
        (see `aget_tools` for semantics).
        """
        return asyncio.run(self.aget_tools(server_name=server_name, tool_name=tool_name))

    def get_resources(self, server_name: str) -> List[Any]:
        return asyncio.run(self.aget_resources(server_name))

    def get_prompts(self, server_name: str, prompt_name: str) -> List[Any]:
        return asyncio.run(self.aget_prompts(server_name, prompt_name))

    # `get_tool` helper removed; use `get_tools(server_name=..., tool_name=...)` instead.

    # ------------------------------------------------------------------

    def list_servers(self) -> List[str]:
        return list(self.server_map.keys())

    def get_client(self) -> MultiServerMCPClient:
        """Return the underlying MultiServerMCPClient instance (sync)."""
        return self.client

    def list_tools(self) -> List[str]:
        """Return a list of tool names (sync)."""
        tools = self.get_tools()
        try:
            # StructuredTool from langchain has `name` attribute
            return [getattr(t, "name", str(t)) for t in tools]
        except Exception:
            return [str(t) for t in tools]

    def get_all_resources(self) -> Dict[str, Any]:
        """Retrieve resources from all configured servers and return a mapping.

        This runs each `get_resources` sequentially (sync wrapper) and collects
        results per-server. It is kept sync for convenience in scripts.
        """
        results: Dict[str, Any] = {}
        for server in self.list_servers():
            try:
                results[server] = self.get_resources(server)
            except Exception as e:
                # capture exception per-server instead of failing whole call
                results[server] = {"error": repr(e)}
        return results

    # ------------------------------------------------------------------
    # --- Unified async tool execution (direct run via tool.arun) ---
    async def aexecute_tool(
        self,
        server_name: str,
        tool_name: str,
        payload: Optional[Dict[str, Any]] = None,
        sanitize: bool = True,
    ) -> Any:
        """
        Execute a tool from a specific MCP server by running its `arun()` method.

        Args:
            server_name: MCP server name (e.g., "google-sheet-server")
            tool_name: Tool name (e.g., "call_google_sheet_tool")
            payload: Dict of arguments passed to the tool
            sanitize: Whether to clean result from 'additionalProperties'

        Returns:
            Any: Result from tool.arun(payload)
        """
        self._validate_server_name(server_name)
        payload = payload or {}

        tools = await self.aget_tools(server_name=server_name)
        matched_tool = next(
            (t for t in tools if self._matches_tool_name(t, tool_name)),
            None
        )

        if matched_tool is None:
            raise ValueError(
                f"Tool '{tool_name}' not found on server '{server_name}'. "
                f"Available: {[getattr(t, 'name', None) for t in tools]}"
            )

        if not hasattr(matched_tool, "arun") or not inspect.iscoroutinefunction(matched_tool.arun):
            raise RuntimeError(
                f"Tool '{tool_name}' from server '{server_name}' "
                f"does not implement async method 'arun(payload)'."
            )

        try:
            result = await matched_tool.arun(payload)
        except Exception as e:
            raise RuntimeError(
                f"Execution of tool '{tool_name}' on server '{server_name}' failed: {e}"
            ) from e

        return self._remove_additional_properties(result) if sanitize else result

    def _validate_server_name(self, name: str) -> None:
        if name not in self.server_map:
            raise ValueError(
                f"Unknown server '{name}'. Known servers: {self.list_servers()}"
            )

