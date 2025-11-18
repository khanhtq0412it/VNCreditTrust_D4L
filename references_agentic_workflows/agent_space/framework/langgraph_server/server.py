"""
Lightweight LangGraph server for running agents in `agents/` and inspecting step-by-step state.

This server exposes simple endpoints to list agents and run a chosen agent's compiled `app` (if present) and returns the sequence of steps produced by the graph's async stream.

It is intentionally dependency-light. Install the optional runtime deps before use:

pip install fastapi uvicorn

Run with:

uvicorn framework.langgraph_server.server:app --host 0.0.0.0 --port 8000

Notes about Langsmith / tracing:
- This server returns the step-by-step state and messages produced by the graph. To observe LLM/tool traces in Langsmith (standalone), configure your environment for LangChain/Langsmith tracing before starting this server. See README in the same folder for instructions.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi import Body
    from pydantic import BaseModel
except Exception:
    # If FastAPI is not installed, export a helpful message on import
    raise RuntimeError("FastAPI (and pydantic) are required to run the langgraph server. Install with: pip install fastapi pydantic uvicorn")

# App
app = FastAPI(title="LangGraph Server for agents/")

ROOT = Path(__file__).resolve().parents[3]  # repository root
AGENTS_DIR = ROOT / "agents"


class RunRequest(BaseModel):
    initial_state: Optional[Dict[str, Any]] = None
    # placeholder for future options
    options: Optional[Dict[str, Any]] = None


def discover_agent_graphs() -> Dict[str, Path]:
    """Scan the `agents/` directory and find agent folders that contain a `graph.py` file."""
    agents = {}
    if not AGENTS_DIR.exists():
        return agents

    for child in AGENTS_DIR.iterdir():
        if child.is_dir():
            gp = child / "graph.py"
            if gp.exists():
                agents[child.name] = gp
    return agents


def load_graph_module(graph_path: Path):
    """Dynamically import a graph module by path and return the module object."""
    name = f"agents_graph_{graph_path.parent.name}"
    spec = importlib.util.spec_from_file_location(name, str(graph_path))
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)
    return module


async def run_graph_and_collect(graph_module, initial_state: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Run the graph's compiled `app` by streaming `app.astream(initial_state)` and collect step outputs.

    Returns a list of step dicts: [{node_name: { ... node state ...}}, ...]
    """
    # Attempt to find a compiled app in the module (common name is `app`)
    app_obj = getattr(graph_module, "app", None)
    if app_obj is None:
        # some agents provide `workflow` instead of compiled `app`
        app_obj = getattr(graph_module, "workflow", None)
    if app_obj is None:
        raise ValueError("Graph module does not define a compiled 'app' or 'workflow' object")

    steps = []

    # The graph library yields async iterator of step dicts via app.astream
    try:
        async for step in app_obj.astream(initial_state or {}):
            # Normalize messages for JSON
            normalized = {}
            for node_name, node_state in step.items():
                # node_state is typically a dict
                ns = {}
                # copy selected fields for inspectability
                for k, v in node_state.items():
                    # messages are often objects (HumanMessage/SystemMessage). Extract `.content` if present.
                    if k == "messages" and isinstance(v, list):
                        msgs = []
                        for m in v:
                            try:
                                content = getattr(m, "content", m)
                            except Exception:
                                content = str(m)
                            msgs.append(content)
                        ns[k] = msgs
                    else:
                        # try json serializable conversion
                        try:
                            json.dumps(v)
                            ns[k] = v
                        except Exception:
                            # fallback to string repr for non-serializable values
                            ns[k] = str(v)
                normalized[node_name] = ns

            steps.append(normalized)
    except Exception as e:
        # capture exception as a final step
        steps.append({"__error__": str(e)})

    return steps


@app.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """Return available agents (folders containing `graph.py`)."""
    agents = discover_agent_graphs()
    return {"agents": list(agents.keys())}


@app.post("/run/{agent_name}")
async def run_agent(agent_name: str, request: RunRequest = Body(...)) -> Dict[str, Any]:
    """Run the named agent and return the sequence of steps.

    Body: { initial_state?: {...} }
    """
    agents = discover_agent_graphs()
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    graph_path = agents[agent_name]

    try:
        module = load_graph_module(graph_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load graph module: {e}")

    try:
        steps = await run_graph_and_collect(module, request.initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running graph: {e}")

    return {"agent": agent_name, "steps": steps}


if __name__ == "__main__":
    import uvicorn

    print("Starting LangGraph server for agents/ on http://0.0.0.0:8000")
    uvicorn.run("framework.langgraph_server.server:app", host="0.0.0.0", port=8000, log_level="info")
