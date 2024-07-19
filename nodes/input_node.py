class InputNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_int": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1, "display": "number"})
            }
        }

    RETURN_TYPES = ("INT",)
    FUNCTION = "process_input"
    CATEGORY = "Custom Nodes"

    def process_input(self, input_int):
        self.input_value = input_int
        return (input_int,)

NODE_CLASS_MAPPINGS = {
    "InputNode": InputNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "InputNode": "Input Node"
}
