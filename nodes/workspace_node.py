import os
from typing import Dict, Any
import json
from aiohttp import web
from PIL import Image


class WorkspaceNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_int": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1, "display": "number"}),
                "workspace_path": ("STRING", {"default": "", "multiline": False, "button": "Select Workspace Path"})
            }
        }

    RETURN_TYPES = ("INT",)
    FUNCTION = "process_workspace"
    CATEGORY = "Custom Nodes"

    def process_workspace(self, input_int, workspace_path):
        # Example processing: double the input integer
        output_int = input_int * 2

        # Load the workspace JSON (if exists) and print its content for now
        if os.path.exists(workspace_path) and workspace_path.endswith(".json"):
            with open(workspace_path, "r") as file:
                workspace_data = json.load(file)
                print(workspace_data)  # You can process this JSON as needed

        return (output_int,)


NODE_CLASS_MAPPINGS = {
    "WorkspaceNode": WorkspaceNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WorkspaceNode": "Workspace Node"
}

# Add custom API routes, using router
from aiohttp import web
from server import PromptServer


@PromptServer.instance.routes.get("/select_workspace_path")
async def select_workspace_path(request):
    # Implement the logic to handle workspace path selection
    return web.json_response({"message": "Workspace path selected"})


# Set the web directory, any .js file in that directory will be loaded by the frontend as a frontend extension
WEB_DIRECTORY = "./somejs"
