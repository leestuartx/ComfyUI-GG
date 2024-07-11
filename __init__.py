import os
import sys
import folder_paths as comfy_paths

# Set up paths
ROOT_PATH = os.path.join(comfy_paths.get_folder_paths("custom_nodes")[0], "ComfyUI-GG")
NODES_PATH = os.path.join(ROOT_PATH, "nodes")
sys.path.append(ROOT_PATH)
sys.path.append(NODES_PATH)

# Import node classes
from .nodes.add_padding_to_image import AddPaddingToImage
from .nodes.metadata_extract_by_seed import MetadataExtractorBySeed
from .nodes.resize_image_proportionally import ResizeImageProportionally
from .nodes.image_metadata_extractor import ImageMetadataExtractor
from .nodes.workspace_node import WorkspaceNode

# Node mappings
NODE_CLASS_MAPPINGS = {
    "AddPaddingToImage": AddPaddingToImage,
    "MetadataExtractBySeed": MetadataExtractorBySeed,
    "ResizeImageProportionally": ResizeImageProportionally,
    "ImageMetadataExtractor": ImageMetadataExtractor,
    "WorkspaceNode": WorkspaceNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AddPaddingToImage": "Add Padding to Image",
    "MetadataExtractBySeed": "Metadata Extract by Seed",
    "ResizeImageProportionally": "Resize Image Proportionally",
    "ImageMetadataExtractor": "Image Metadata Extractor",
    "WorkspaceNode": "Workspace Node"
}


__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
