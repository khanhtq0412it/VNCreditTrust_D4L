from langchain_core.runnables.graph import MermaidDrawMethod

def export_workflow_graph(app, output_path: str = "workflow.png", draw_method: MermaidDrawMethod = MermaidDrawMethod.API) -> str:
    """
    Export the execution graph of a LangChain application to a PNG file.

    Args:
        app: A LangChain application or workflow object that implements the `get_graph()` method.
        output_path (str): The destination path for the PNG file. Defaults to "workflow.png".
        draw_method (MermaidDrawMethod): The rendering method to use.
            - Use `MermaidDrawMethod.API` to render via the online Mermaid API (requires internet access).
            - Use `MermaidDrawMethod.LOCAL` to render using a local Mermaid CLI if available.

    Returns:
        str: The path to the saved PNG file.

    Example:
        >>> from my_app import app
        >>> export_workflow_graph(app, "workflow_graph.png")
        ✅ Workflow graph exported to: workflow_graph.png
    """
    png_data = app.get_graph().draw_mermaid_png(draw_method=draw_method)

    with open(output_path, "wb") as f:
        f.write(png_data)

    print(f"✅ Workflow graph exported to: {output_path}")
    return output_path
