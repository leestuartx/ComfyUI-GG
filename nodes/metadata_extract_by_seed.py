import logging
import os
from PIL import Image, ImageOps
import torch
import numpy as np
from sd_parsers import ParserManager  # , PromptInfo
from typing import Any, Dict, List

# Initialize the parser manager
parser_manager = ParserManager()


class MetadataExtractorBySeed:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 0, "min": 0}),
            }
        }

    CATEGORY = "image"

    RETURN_TYPES = (
        "IMAGE", "MASK", "STRING", "FLOAT", "INT", "INT", "INT",
        "STRING", "STRING", "INT", "STRING", "STRING",
        "STRING"
    )
    RETURN_NAMES = (
        "image", "mask", "metadata", "cfg_scale", "steps", "width", "height",
        "positive_prompt", "negative_prompt", "clip_skip",
        "model_name", "filename",
        "raw_metadata"
    )

    FUNCTION = "extract_metadata"

    def extract_metadata(self, directory, seed):
        try:
            # Resolve the directory path
            directory = self._resolve_path(directory)
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not files:
                raise ValueError("No image files found in the directory.")

            # Calculate the index based on the seed
            index = seed % len(files)
            image_path = os.path.join(directory, files[index])

            img = Image.open(image_path)
            transposed_img = ImageOps.exif_transpose(img)
            output_image_array = np.array(transposed_img).astype(np.float32) / 255.0
            output_image = torch.from_numpy(output_image_array)[None,]
            if "A" in transposed_img.getbands():
                mask_array = np.array(transposed_img.getchannel("A")).astype(np.float32) / 255.0
                output_mask = 1.0 - torch.from_numpy(mask_array)
            else:
                output_mask = torch.zeros((64, 64), dtype=torch.float32)

            width, height = img.size
            filename = os.path.basename(image_path)

            # Parse the image directly using the parser manager
            prompt_info = parser_manager.parse(img)
            if prompt_info:
                metadata = self.format_metadata(prompt_info)
                raw_metadata = self.format_raw_metadata(prompt_info)
                cfg_scale = self.get_float(prompt_info.parameters, 'cfg')
                steps = self.get_int(prompt_info.parameters, 'steps')
                positive_prompt = self.get_prompt_text(prompt_info.prompts)
                negative_prompt = self.get_prompt_text(prompt_info.negative_prompts)
                clip_skip = self.get_int(prompt_info.parameters, 'clip')
                model_name = self.get_model_name(prompt_info)

                # Try extracting the positive prompt using the new method
                temp_metadata = self.extract_metadata_type2(image_path)
                metadata_str_keys = self.convert_keys_to_strings(temp_metadata)
                prompt_data = self.find_positive_prompt_data(metadata_str_keys)
                if len(prompt_data) > 0:
                    positive_prompt = prompt_data[0]

                return (
                    output_image, output_mask, metadata, cfg_scale, steps, int(width), int(height),
                    positive_prompt, negative_prompt, clip_skip, model_name,
                    filename, raw_metadata
                )
            else:
                return (
                    output_image, output_mask, "No metadata found.", 0.0, 0, int(width), int(height),
                    "", "", 0, "Unknown",
                    os.path.basename(image_path), ""
                )
        except Exception as e:
            logging.exception("Error processing image")
            return (
                None, None, f"Error processing image: {str(e)}", 0.0, 0, 0, 0,
                "", "", 0, "Unknown",
                "", ""
            )

    def _resolve_path(self, path) -> str:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        return path

    def extract_metadata_type2(self, file_path: str) -> Dict[str, Any]:
        try:
            img = Image.open(file_path)
            # Extract metadata using sd_parsers
            prompt_info = parser_manager.parse(file_path)
            if not prompt_info:
                raise ValueError("No metadata found in image.")
            metadata = {
                "prompt": prompt_info.parameters,
                "workflow": prompt_info.metadata
            }
            return metadata
        except Exception as e:
            raise ValueError(f"Error extracting metadata: {e}")

    def convert_keys_to_strings(self, d):
        if isinstance(d, dict):
            return {str(k): self.convert_keys_to_strings(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self.convert_keys_to_strings(i) for i in d]
        else:
            return d

    def find_positive_prompt_data(self, metadata: Dict[str, Any]) -> List[str]:
        output_data = []

        # Checking in both 'prompt' and 'workflow' sections for relevant nodes
        for key, section in metadata.items():
            if key == 'workflow' and isinstance(section, dict):
                if "nodes" in section:
                    for node in section["nodes"]:
                        if node.get("type") == "ShowText|pysssss" and node.get("properties", {}).get("Node name for S&R") == "ShowText|pysssss":
                            widgets_values = node.get("widgets_values", [])
                            for widget in widgets_values:
                                if isinstance(widget, list):
                                    text_value = widget[0]
                                    output_data.append(text_value)

            elif isinstance(section, dict):
                for subkey, subsection in section.items():
                    if subkey == 'workflow' and isinstance(subsection, dict):
                        if "nodes" in subsection:
                            for node in subsection["nodes"]:
                                if node.get("type") == "ShowText|pysssss" and node.get("properties", {}).get("Node name for S&R") == "ShowText|pysssss":
                                    widgets_values = node.get("widgets_values", [])
                                    for widget in widgets_values:
                                        if isinstance(widget, list):
                                            text_value = widget[0]
                                            output_data.append(text_value)

        return output_data

    def format_metadata(self, prompt_info):
        metadata_parts = []

        # Models
        if prompt_info.models:
            model_text = '\n'.join([model.name for model in prompt_info.models])
            metadata_parts.append(f"Models:\n{model_text}")

        # Samplers
        if prompt_info.samplers:
            sampler_names = '\n'.join([sampler.name for sampler in prompt_info.samplers])
            metadata_parts.append(f"Samplers:\n{sampler_names}")
            for sampler in prompt_info.samplers:
                for param, value in sampler.parameters.items():
                    metadata_parts.append(f"{param.title()}: {value}")

        # Prompts
        if prompt_info.prompts:
            prompt_text = '\n'.join([prompt.value for prompt in prompt_info.prompts])
            metadata_parts.append(f"Prompts:\n{prompt_text}")

        # Negative Prompts
        if prompt_info.negative_prompts:
            negative_prompt_text = '\n'.join([prompt.value for prompt in prompt_info.negative_prompts])
            metadata_parts.append(f"Negative Prompts:\n{negative_prompt_text}")

        # Additional metadata
        if prompt_info.metadata:
            additional_metadata = '\n'.join([f"{k}: {v}" for k, v in prompt_info.metadata.items()])
            metadata_parts.append(f"Additional Metadata:\n{additional_metadata}")

        # Unmodified parameters
        if prompt_info.parameters:
            params_text = '\n'.join([f"{k}: {v}" for k, v in prompt_info.parameters.items()])
            metadata_parts.append(f"Parameters:\n{params_text}")

        return '\n\n'.join(metadata_parts)

    def format_raw_metadata(self, prompt_info):
        return str(prompt_info)

    def get_float(self, parameters, key):
        try:
            value = str(parameters.get(key, '0.0')).strip()
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def get_int(self, parameters, key):
        try:
            value = str(parameters.get(key, '0')).strip()
            return int(value)
        except (ValueError, TypeError):
            return 0

    def get_prompt_text(self, prompts):
        if prompts:
            return '\n'.join([prompt.value for prompt in prompts])
        return ""

    def get_model_name(self, prompt_info):
        if isinstance(prompt_info.models, list) and len(prompt_info.models) > 0:
            return prompt_info.models[0].name
        return ""


NODE_CLASS_MAPPINGS = {
    "MetadataExtractorBySeed": MetadataExtractorBySeed
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MetadataExtractorBySeed": "Image Metadata Extractor By Seed"
}
