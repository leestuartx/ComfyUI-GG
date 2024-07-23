import server

class ForLoopNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "start": ("INT", {"default": 0, "min": 0}),
                "end": ("INT", {"default": 10, "min": 0}),
                "current_index": ("INT", {"default": 0, "min": 0}),
                "iterations": ("INT", {"default": 0, "min": 0}),
            },
            "hidden": {"my_unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("current_index", "iterations")
    FUNCTION = "increment_index"
    CATEGORY = "GG/Loop"
    OUTPUT_NODE = True

    def increment_index(self, start, end, current_index, iterations, my_unique_id=None):
        if current_index < end:
            current_index += 1
        else:
            current_index = start  # Reset to start if it reaches end
            iterations += 1  # Increment iterations when the loop reaches the end

        # Send the updated current_index and iterations to the server
        server.PromptServer.instance.send_sync(
            "update-current-index",
            {"node_id": my_unique_id, "current_index": current_index, "iterations": iterations}
        )

        return (current_index, iterations)

# Node Mappings
NODE_CLASS_MAPPINGS = {
    "ForLoopNode": ForLoopNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ForLoopNode": "For Loop"
}