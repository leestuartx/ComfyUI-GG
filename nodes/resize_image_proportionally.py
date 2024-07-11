from PIL import Image, ImageOps
import numpy as np
import torch


class ResizeImageProportionally:
    resampling_methods = {
        "NEAREST": Image.Resampling.NEAREST,
        "BILINEAR": Image.Resampling.BILINEAR,
        "BICUBIC": Image.Resampling.BICUBIC,
        "LANCZOS": Image.Resampling.LANCZOS,
    }

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_width": ("INT", {"default": 1920, "min": 1, "step": 1}),
                "resampling_method": (["NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"], {"default": "BILINEAR"}),
            }
        }

    CATEGORY = "image"

    RETURN_TYPES = ("IMAGE", "IMAGE", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("original_image", "resized_image", "target_width", "target_height", "original_width", "original_height")

    FUNCTION = "resize_image"

    def resize_image(self, image, target_width, resampling_method):
        try:
            # Convert tensor image to numpy array
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0])

            # Transpose the image based on EXIF data
            transposed_img = ImageOps.exif_transpose(img)

            # Get original dimensions
            original_width, original_height = transposed_img.size

            # Calculate the aspect ratio and new height
            aspect_ratio = original_height / original_width
            target_height = int(target_width * aspect_ratio)

            # Resize the image
            resampling = self.resampling_methods[resampling_method]
            resized_img = transposed_img.resize((target_width, target_height), resampling)

            # Convert resized image to the same format as the input
            resized_image_array = np.array(resized_img).astype(np.float32) / 255.0
            resized_image_tensor = torch.from_numpy(resized_image_array).unsqueeze(0)

            return image, resized_image_tensor, target_width, target_height, original_width, original_height

        except Exception as e:
            return f"Error processing image: {str(e)}", None, 0, 0, 0, 0


NODE_CLASS_MAPPINGS = {
    "ResizeImageProportionally": ResizeImageProportionally
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ResizeImageProportionally": "Resize Image Proportionally"
}
