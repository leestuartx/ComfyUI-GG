import importlib.util
import os
import json

class WorkspaceNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_int": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1, "display": "number"}),
                "workspace_path": ("STRING", {"default": "", "multiline": False, "button": "Select Workspace Path"})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_workspace"
    CATEGORY = "Custom Nodes"

    def process_workspace(self, input_int, workspace_path):
        if not os.path.exists(workspace_path) or not workspace_path.endswith(".json"):
            raise ValueError("Invalid workspace path")

        with open(workspace_path, "r") as file:
            workflow = json.load(file)

        # Inject input_int into the InputNode
        for node in workflow["nodes"]:
            if node["type"] == "InputNode":
                node["properties"]["input_int"] = input_int

        # Print the workflow JSON data
        print(json.dumps(workflow, indent=4))

        return (json.dumps(workflow, indent=4),)

NODE_CLASS_MAPPINGS = {
    "WorkspaceNode": WorkspaceNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WorkspaceNode": "Workspace Node"
}

def load_custom_nodes(custom_nodes_path="custom_nodes"):
    for filename in os.listdir(custom_nodes_path):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            module_path = os.path.join(custom_nodes_path, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for class_name, cls in module.NODE_CLASS_MAPPINGS.items():
                NODE_CLASS_MAPPINGS[class_name] = cls
            for display_name, display_value in module.NODE_DISPLAY_NAME_MAPPINGS.items():
                NODE_DISPLAY_NAME_MAPPINGS[display_name] = display_value

def execute_node(node):
    node_type = node["type"]
    if node_type in NODE_CLASS_MAPPINGS:
        node_class = NODE_CLASS_MAPPINGS[node_type]
        node_instance = node_class()
        func = getattr(node_instance, node_class.FUNCTION)
        input_args = node["properties"]
        output = func(**input_args)
        return output
    else:
        raise ValueError(f"Unknown node type: {node_type}")

def load_and_process_workflow(main_workflow_path):
    with open(main_workflow_path, "r") as file:
        main_workflow = json.load(file)

    for node in main_workflow["nodes"]:
        if node["type"] == "WorkspaceNode":
            workspace_node = WorkspaceNode()
            input_int = node["properties"]["input_int"]
            workspace_path = node["properties"]["workspace_path"]
            workspace_workflow = workspace_node.process_workspace(input_int, workspace_path)

            main_workflow["nodes"].extend(workspace_workflow["nodes"])

    for node in main_workflow["nodes"]:
        execute_node(node)

    return main_workflow
