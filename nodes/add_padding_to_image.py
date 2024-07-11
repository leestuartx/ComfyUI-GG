from PIL import Image, ImageOps
import numpy as np
import torch


class AddPaddingToImage:
    aspect_ratios = [
        "Use Image Resolution", "1:1 (square)", "4:3 (landscape)", "3:2 (landscape)",
        "16:9 (landscape)", "21:9 (landscape)", "3:4 (portrait)",
        "2:3 (portrait)", "9:16 (portrait)", "9:21 (portrait)"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "aspect_ratio": (cls.aspect_ratios,)
            }
        }

    CATEGORY = "image"

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("padded_image", "padding_left", "padding_right", "padding_top", "padding_bottom")

    FUNCTION = "add_padding"

    def add_padding(self, image, aspect_ratio):
        try:
            # Convert tensor image to numpy array
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0])

            # Transpose the image based on EXIF data
            transposed_img = ImageOps.exif_transpose(img)

            # Get original dimensions
            width, height = transposed_img.size

            if aspect_ratio == "Use Image Resolution":
                new_width, new_height = width, height
            else:
                new_width, new_height = self.get_new_dimensions(aspect_ratio, width, height)

            padding_left = max(0, (new_width - width) // 2)
            padding_right = max(0, new_width - width - padding_left)
            padding_top = max(0, (new_height - height) // 2)
            padding_bottom = max(0, new_height - height - padding_top)

            padded_img = ImageOps.expand(transposed_img, (padding_left, padding_top, padding_right, padding_bottom), fill='black')
            padded_image_array = np.array(padded_img).astype(np.float32) / 255.0
            padded_image = torch.from_numpy(padded_image_array).unsqueeze(0)

            return padded_image, padding_left, padding_right, padding_top, padding_bottom
        except Exception as e:
            return None, 0, 0, 0, 0

    def get_new_dimensions(self, aspect_ratio, width, height):
        aspect_ratio_map = {
            "1:1 (square)": (1, 1),
            "4:3 (landscape)": (4, 3),
            "3:2 (landscape)": (3, 2),
            "16:9 (landscape)": (16, 9),
            "21:9 (landscape)": (21, 9),
            "3:4 (portrait)": (3, 4),
            "2:3 (portrait)": (2, 3),
            "9:16 (portrait)": (9, 16),
            "9:21 (portrait)": (9, 21)
        }

        target_ratio = aspect_ratio_map[aspect_ratio]
        target_width, target_height = target_ratio

        width_ratio = width / target_width
        height_ratio = height / target_height

        if width_ratio > height_ratio:
            new_width = width
            new_height = int(width * target_height / target_width)
        else:
            new_height = height
            new_width = int(height * target_width / target_height)

        return new_width, new_height


NODE_CLASS_MAPPINGS = {
    "AddPaddingToImage": AddPaddingToImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AddPaddingToImage": "Add Padding to Image"
}
