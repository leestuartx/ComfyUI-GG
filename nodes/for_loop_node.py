import server
from .common.config import MAX_SEED_NUM

class ForLoopNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "start": ("INT", {"default": 0, "min": 0}),
                "end": ("INT", {"default": 10, "min": 0}),
                "current_index": ("INT", {"default": 0, "min": 0}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO", "my_unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("current_index",)
    FUNCTION = "increment_index"
    CATEGORY = "GG/Loop"
    OUTPUT_NODE = True

    def increment_index(self, start, end, current_index, prompt=None, extra_pnginfo=None, my_unique_id=None):
        has_changed = False
        if current_index < end:
            current_index += 1
            has_changed = True
        else:
            current_index = end # start  # Reset to start if it reaches end

        if has_changed == True:
            # Send the updated current_index to the server
            server.PromptServer.instance.send_sync(
                "update-current-index",
                {"node_id": my_unique_id, "current_index": current_index}
            )

        return (current_index,)

# Node Mappings
NODE_CLASS_MAPPINGS = {
    "ForLoopNode": ForLoopNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ForLoopNode": "For Loop"
}
