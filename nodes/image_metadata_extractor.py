import os
from PIL import Image, ImageOps
import torch
import numpy as np
from sd_parsers import ParserManager  # , PromptInfo
import folder_paths
from typing import Any, Dict, List

# Initialize the parser manager
parser_manager = ParserManager()


class ImageMetadataExtractor:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True})
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

    def extract_metadata(self, image):

        image_path = folder_paths.get_annotated_filepath(image)
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

        metadata = ''
        raw_metadata = ''
        cfg_scale = 0
        steps = 0

        positive_prompt = ''
        negative_prompt = ''
        clip_skip = 0
        model_name = ''

        # Parse the image directly using the parser manager
        prompt_info = None

        try:
            prompt_info = parser_manager.parse(img)
            print(prompt_info)

            if prompt_info:
                print('There is metadata')
                try:
                    metadata = self.format_metadata(prompt_info)
                except:
                    print('cant parse metadata')

                try:
                    raw_metadata = self.format_raw_metadata(prompt_info)
                except:
                    print('cant parse raw metadata')

                try:
                    cfg_scale = self.get_float(prompt_info.parameters, 'cfg')
                except:
                    print('cant parse cfg scale')

                try:
                    steps = self.get_int(prompt_info.parameters, 'steps')
                except:
                    pass
                try:
                    positive_prompt = self.get_prompt_text(prompt_info.prompts)
                except:
                    print('cant parse positive prompt')
                try:
                    negative_prompt = self.get_prompt_text(prompt_info.negative_prompts)
                except:
                    pass

                try:
                    clip_skip = self.get_int(prompt_info.parameters, 'clip')
                except:
                    pass
                try:
                    model_name = ''  # self.get_model_name(prompt_info)
                except:
                    pass
        except:
            print('could not parse default metadata')

        # Try extracting the positive prompt using the new method
        temp_metadata = self.extract_metadata_type2(image_path)
        metadata_str_keys = self.convert_keys_to_strings(temp_metadata)
        if metadata_str_keys:
            prompt_data = self.find_positive_prompt_data(metadata_str_keys)
            if len(prompt_data) > 0:
                positive_prompt = prompt_data[0]

        return (
            output_image, output_mask, metadata, cfg_scale, steps, int(width), int(height),
            positive_prompt, negative_prompt, clip_skip, model_name,
            filename, raw_metadata
        )


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
                else:
                    for subkey, subsection in section.items():
                        if subkey == 'workflow' and isinstance(subsection, dict):
                            print(subsection)
                            if "nodes" in subsection:
                                print('found nodes')
                                for node in subsection["nodes"]:
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
        if hasattr(prompt_info, 'models') and prompt_info.models:
            model_text = '\n'.join([model.name for model in prompt_info.models])
            metadata_parts.append(f"Models:\n{model_text}")

        # Samplers
        if hasattr(prompt_info, 'samplers') and prompt_info.samplers:
            sampler_names = '\n'.join([sampler.name for sampler in prompt_info.samplers])
            metadata_parts.append(f"Samplers:\n{sampler_names}")
            for sampler in prompt_info.samplers:
                for param, value in sampler.parameters.items():
                    metadata_parts.append(f"{param.title()}: {value}")

        # Prompts
        if hasattr(prompt_info, 'prompts') and prompt_info.prompts:
            prompt_text = '\n'.join([prompt.value for prompt in prompt_info.prompts])
            metadata_parts.append(f"Prompts:\n{prompt_text}")

        # Negative Prompts
        if hasattr(prompt_info, 'negative_prompts') and prompt_info.negative_prompts:
            negative_prompt_text = '\n'.join([prompt.value for prompt in prompt_info.negative_prompts])
            metadata_parts.append(f"Negative Prompts:\n{negative_prompt_text}")

        # Additional metadata
        if hasattr(prompt_info, 'metadata') and prompt_info.metadata:
            additional_metadata = '\n'.join([f"{k}: {v}" for k, v in prompt_info.metadata.items()])
            metadata_parts.append(f"Additional Metadata:\n{additional_metadata}")

        # Unmodified parameters
        if hasattr(prompt_info, 'parameters') and prompt_info.parameters:
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


NODE_CLASS_MAPPINGS = {
    "ImageMetadataExtractor": ImageMetadataExtractor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMetadataExtractor": "Image Metadata Extractor"
}
