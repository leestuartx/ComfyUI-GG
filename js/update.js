import { api } from "../../../scripts/api.js";

function updateCurrentIndexHandler(event) {
    let nodes = app.graph._nodes_by_id;
    let data = event.detail;
    let node = nodes[data.node_id];

    if (node) {
        const widget = node.widgets.find(w => w.name === 'current_index');
        if (widget) {
            widget.value = data.current_index;
            app.canvas.setDirty(true, true);
        }
    }
}

api.addEventListener("update-current-index", updateCurrentIndexHandler);
