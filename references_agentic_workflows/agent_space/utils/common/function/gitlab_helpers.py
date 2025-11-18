import json
import base64


async def _get_repository_tree(mcp, project_id: str, path: str, ref: str, recursive: bool, per_page: int):
    payload = {"project_id": project_id, "path": path, "ref": ref, "recursive": recursive, "per_page": per_page}
    result = await mcp.aexecute_tool("gitlab_vetc-server", "get_repository_tree", payload)
    return json.loads(result)


async def _get_file_content(mcp, project_id: str, file_path: str, ref: str = "main") -> str:
    payload = {"project_id": project_id, "file_path": file_path, "ref": ref}
    raw_result = await mcp.aexecute_tool("gitlab_vetc-server", "get_file_contents", payload)
    data = json.loads(raw_result)
    if isinstance(data, str):
        return data
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8")
    return data.get("content", "")


async def get_dbt_model_logic(mcp, model_name: str, project_id: str, path: str = "models/staging", ref: str = "main"):
    target_file = f"{model_name}.sql"
    tree = await _get_repository_tree(mcp, project_id, path, ref, recursive=True, per_page=500)
    matched_files = [item for item in tree if item.get("type") == "blob" and item.get("name") == target_file]
    if not matched_files:
        raise FileNotFoundError(f"Không tìm thấy file model '{target_file}' trong path '{path}'")
    file_path = matched_files[0]["path"]
    return await _get_file_content(mcp, project_id, file_path, ref)


async def get_dbt_model_schema(mcp, model_name: str, project_id: str, path: str = "models/staging", ref: str = "main"):
    possible_files = [f"schema_{model_name}.yaml", f"{model_name}_schema.yaml", f"schema_{model_name}.yml", f"{model_name}_schema.yml"]
    tree = await _get_repository_tree(mcp, project_id, path, ref, recursive=True, per_page=500)
    matched_files = [item for item in tree if item.get("type") == "blob" and item.get("name") in possible_files]
    if not matched_files:
        raise FileNotFoundError(f"Không tìm thấy schema file cho model '{model_name}' trong path '{path}'")
    return await _get_file_content(mcp, project_id, matched_files[0]["path"], ref)
