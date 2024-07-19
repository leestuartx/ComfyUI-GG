class OutputNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "output_int": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1, "display": "number"})
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "process_output"
    CATEGORY = "Custom Nodes"

    def process_output(self, output_int):
        self.output_value = output_int
        return ()

NODE_CLASS_MAPPINGS = {
    "OutputNode": OutputNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OutputNode": "Output Node"
}
