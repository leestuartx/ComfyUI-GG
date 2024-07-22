import logging
from sd_parsers import ParserManager, PromptInfo
from PIL import Image
from typing import Any, Dict, List, Union

class MetadataParser:
    def __init__(self):
        self.parser_manager = ParserManager()

    def extract_metadata(self, image_path: str):
        try:
            img = Image.open(image_path)
            prompt_info = self.parser_manager.parse(img)
            if prompt_info:
                metadata = self.format_metadata(prompt_info)
                cfg_scale = self.find_value_in_dict(prompt_info.parameters, 'cfg')
                steps = self.find_value_in_dict(prompt_info.parameters, 'steps')
                vaes = self.find_values_in_dict(prompt_info.parameters, 'vae_name')
                models = [model['content'] if isinstance(model, dict) else model for model in self.find_values_in_dict(prompt_info.parameters, 'ckpt_name')]
                sampler_name = self.find_value_in_dict(prompt_info.parameters, 'sampler_name')
                scheduler = self.find_value_in_dict(prompt_info.parameters, 'scheduler')
                denoise = self.find_value_in_dict(prompt_info.parameters, 'denoise')
                width, height = img.size

                temp_metadata = self.extract_metadata_type2(image_path)
                metadata_str_keys = self.convert_keys_to_strings(temp_metadata)

                prompt_data = self.find_positive_prompt_data(metadata_str_keys)
                positive_prompt = ""
                if len(prompt_data) > 0:
                    positive_prompt = prompt_data[0]


                negative_prompt = self.get_prompt_text(prompt_info.negative_prompts)
                clip_skip = self.find_value_in_dict(prompt_info.parameters, 'clip')
                return prompt_info, metadata, cfg_scale, steps, width, height, positive_prompt, negative_prompt, clip_skip, vaes, models, sampler_name, scheduler, denoise
            else:
                return prompt_info, "No metadata found.", 0.0, 0, 0, 0, "", "", 0, [], [], "", "", 0.0
        except Exception as e:
            logging.exception("Error processing image")
            return f"Error processing image: {str(e)}", "", 0.0, 0, 0, 0, "", "", 0, [], [], "", "", 0.0

    def extract_metadata_type2(self, file_path: str) -> Dict[str, Any]:
        try:
            img = Image.open(file_path)
            # Extract metadata using sd_parsers
            prompt_info = self.parser_manager.parse(file_path)
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

    def find_value_in_dict(self, d: Union[Dict, List], key: str, default=None) -> Any:
        if isinstance(d, dict):
            for k, v in d.items():
                if k == key:
                    return v
                elif isinstance(v, (dict, list)):
                    result = self.find_value_in_dict(v, key, default)
                    if result is not None:
                        return result
        elif isinstance(d, list):
            for item in d:
                result = self.find_value_in_dict(item, key, default)
                if result is not None:
                    return result
        return default

    def find_values_in_dict(self, d: Union[Dict, List], key: str) -> List[Any]:
        values = []
        if isinstance(d, dict):
            for k, v in d.items():
                if k == key:
                    values.append(v)
                elif isinstance(v, (dict, list)):
                    values.extend(self.find_values_in_dict(v, key))
        elif isinstance(d, list):
            for item in d:
                values.extend(self.find_values_in_dict(item, key))
        return values

    def format_metadata(self, prompt_info: PromptInfo):
        metadata_parts = []

        models = [model['content'] if isinstance(model, dict) else model for model in self.find_values_in_dict(prompt_info.parameters, 'ckpt_name')]
        if models:
            model_text = '\n'.join(models)
            metadata_parts.append(f"Models:\n{model_text}")

        vaes = self.find_values_in_dict(prompt_info.parameters, 'vae_name')
        if vaes:
            vae_text = '\n'.join(vaes)
            metadata_parts.append(f"VAEs:\n{vae_text}")

        if prompt_info.samplers:
            sampler_names = '\n'.join([sampler.name for sampler in prompt_info.samplers])
            metadata_parts.append(f"Samplers:\n{sampler_names}")
            for sampler in prompt_info.samplers:
                for param, value in sampler.parameters.items():
                    metadata_parts.append(f"{param.title()}: {value}")

        if prompt_info.prompts:
            prompt_text = '\n'.join([prompt.value for prompt in prompt_info.prompts])
            metadata_parts.append(f"Prompts:\n{prompt_text}")

        if prompt_info.negative_prompts:
            negative_prompt_text = '\n'.join([prompt.value for prompt in prompt_info.negative_prompts])
            metadata_parts.append(f"Negative Prompts:\n{negative_prompt_text}")

        if prompt_info.metadata:
            additional_metadata = '\n'.join([f"{k}: {v}" for k, v in prompt_info.metadata.items()])
            metadata_parts.append(f"Additional Metadata:\n{additional_metadata}")

        if prompt_info.parameters:
            params_text = '\n'.join([f"{k}: {v}" for k, v in prompt_info.parameters.items()])
            metadata_parts.append(f"Parameters:\n{params_text}")

        return '\n\n'.join(metadata_parts)

    def get_prompt_text(self, prompts):
        if prompts:
            return '\n'.join([prompt.value for prompt in prompts])
        return ""

    def find_positive_prompt_data(self, metadata: Dict[str, Any]) -> List[str]:
        output_data = []

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
