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


NODE_CLASS_MAPPINGS = {
    "ImageMetadataExtractor": ImageMetadataExtractor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMetadataExtractor": "Image Metadata Extractor"
}
