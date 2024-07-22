import logging
import os
from PIL import Image, ImageOps
import torch
import numpy as np
from sd_parsers import ParserManager  # , PromptInfo
from typing import Any, Dict, List
from common.metadata_parser import MetadataParser

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

            parser = MetadataParser()
            prompt_info, formatted_metadata, cfg_scale, steps, width, height, positive_prompt, negative_prompt, clip_skip, vaes, models, sampler_name, scheduler, denoise = parser.extract_metadata(image_path)

            model_name = ', '.join(models)

            try:
                prompt_info = parser_manager.parse(img)
                metadata = parser.format_metadata(prompt_info)
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


NODE_CLASS_MAPPINGS = {
    "MetadataExtractorBySeed": MetadataExtractorBySeed
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MetadataExtractorBySeed": "Image Metadata Extractor By Seed"
}
