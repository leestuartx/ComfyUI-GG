import random
import server
import logging
from enum import Enum

class SGmode(Enum):
    FIX = 1
    INCR = 2
    DECR = 3
    RAND = 4

def control_index(v, action):
    if action == 'increment':
        v['inputs']['current_index'] += 1
    elif action == 'decrement':
        v['inputs']['current_index'] -= 1
    elif action == 'randomize':
        v['inputs']['current_index'] = random.randint(v['inputs']['start'], v['inputs']['end'])
    return v['inputs']['current_index']

def prompt_index_update(json_data):
    workflow = json_data['extra_data']['extra_pnginfo']['workflow']
    value = None
    action = None
    node = None

    for k, v in json_data['prompt'].items():
        if 'class_type' not in v:
            continue

        cls = v['class_type']

        if cls == 'ForLoopNode':
            action = 'increment'
            value = v['inputs']['current_index']
            node = k, v

    if node is not None:
        value = control_index(node[1], action)

    return value is not None

def workflow_index_update(json_data):
    nodes = json_data['extra_data']['extra_pnginfo']['workflow']['nodes']
    prompt = json_data['prompt']

    updated_index_map = {}
    value = None

    for node in nodes:
        node_id = str(node['id'])
        if node_id in prompt:
            if node['type'] == 'ForLoopNode':
                value = prompt[node_id]['inputs']['current_index']
                prompt[node_id]['widgets_values'][0] = value
                updated_index_map[node_id] = value

    server.PromptServer.instance.send_sync("update-current-index", {"id": node_id, "value": value, "index_map": updated_index_map})

def onprompt(json_data):
    is_changed = prompt_index_update(json_data)
    if is_changed:
        workflow_index_update(json_data)

    return json_data

server.PromptServer.instance.add_on_prompt_handler(onprompt)


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}