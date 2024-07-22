import os
from PIL import Image, ImageOps
import torch
import numpy as np
from sd_parsers import ParserManager, PromptInfo
import folder_paths
from typing import Any, Dict, List
from common.metadata_parser import MetadataParser

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

        parser = MetadataParser()
        prompt_info, formatted_metadata, cfg_scale, steps, width, height, positive_prompt, negative_prompt, clip_skip, vaes, models, sampler_name, scheduler, denoise = parser.extract_metadata(image_path)

        model_name = ', '.join(models)

        try:
            prompt_info = parser_manager.parse(img)
            metadata = self.format_metadata(prompt_info)
            raw_metadata = str(prompt_info)
        except Exception as e:
            print('Error extracting metadata:', e)
            metadata = ''
            raw_metadata = ''

        return (
            output_image, output_mask, metadata, cfg_scale, steps, int(width), int(height),
            positive_prompt, negative_prompt, clip_skip, model_name,
            filename, raw_metadata
        )

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


NODE_CLASS_MAPPINGS = {
    "ImageMetadataExtractor": ImageMetadataExtractor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMetadataExtractor": "Image Metadata Extractor"
}
