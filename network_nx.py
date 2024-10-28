import pandas as pd
from pyvis.network import Network
import html

# Sample DataFrame for port_gate_df
port_gate_data = {
    'port_id': [0, 1, 2, 3],
    'port_type': ['load', 'discharge', 'term_source', 'term_sink'],
    'gate_name': ['G1', 'G1', 'G2', 'G2'],
    'travel_days': ['0 1', '0 2', '0 3', '0 4']  # Note the format '0 1'
}
port_gate_df = pd.DataFrame(port_gate_data)

# Sample DataFrame for port_route_df with all possible combinations except (0,0), (1,1), (2,2), (3,3)
route_data = {
    'startport': [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3],
    'endport': [1, 2, 3, 1, 0, 2, 3, 0, 0, 1, 3, 1, 0, 1, 2, 0],
    'passby_gate': ['G1,G2', 'G1,G2', 'G1,G2', 'G1,G2', 'G1', 'G1', 'G1', 'G1', 'G2', 'G2', 'G2', 'G2', 'G2', 'G2', 'G2', 'G2']
}
port_route_df = pd.DataFrame(route_data)

# Sample DataFrame for gate_attribute_df
gate_attribute_data = {
    'gate_name': ['G1', 'G2'],
    'waitdays': ['0 4', '0 0'],  # Note the format '0 4'
    'gate_cost': [1000, 1500]
}
gate_attribute_df = pd.DataFrame(gate_attribute_data)

# Sample DataFrame for gate_to_gate_df
gate_to_gate_data = {
    'Start_Gate': ['G1', 'G1'],
    'End_Gate': ['G2', 'G3'],
    'Transit_Days': [4, 2]
}
gate_to_gate_df = pd.DataFrame(gate_to_gate_data)

# Sample set for current_arcs
current_arcs = {
    "2 term_source 0 load",
    "1 discharge 0 load",
    "1 discharge 3 term_sink",
    "2 term_source 3 term_sink"
}

# Function to extract the last integer from the formatted string
def extract_last_number(s):
    return int(s.split()[-1])

# Function to parse current_arcs and create (startport, endport) tuples
def parse_arcs(arcs):
    tuples = []
    for arc in arcs:
        parts = arc.split()
        startport = int(parts[0])
        endport = int(parts[2])
        tuples.append((startport, endport))
    return tuples

# Calculate total travel days and gate cost for each (startport, endport) combination including waitdays and transit days
travel_days_dict = {}
gate_cost_dict = {}
passby_gates_dict = {}

# Parse current_arcs to get (startport, endport) tuples
combinations = parse_arcs(current_arcs)

for startport, endport in combinations:
    # Get the in-between gates from port_route_df
    route_row = port_route_df[(port_route_df['startport'] == startport) & (port_route_df['endport'] == endport)]
    if route_row.empty:
        continue
    gates = route_row['passby_gate'].iloc[0].split(',')

    total_travel_days = 0
    total_gate_cost = 0

    # Add travel days and gate cost for the start port connection
    start_port_travel_days = port_gate_df.loc[(port_gate_df['port_id'] == startport) & (port_gate_df['gate_name'] == gates[0]), 'travel_days']
    if not start_port_travel_days.empty:
        total_travel_days += extract_last_number(start_port_travel_days.iloc[0])

    for i, gate in enumerate(gates):
        wait_days = gate_attribute_df.loc[gate_attribute_df['gate_name'] == gate, 'waitdays']
        gate_cost = gate_attribute_df.loc[gate_attribute_df['gate_name'] == gate, 'gate_cost']

        if not wait_days.empty:
            total_travel_days += extract_last_number(wait_days.iloc[0])
        if not gate_cost.empty:
            total_gate_cost += gate_cost.iloc[0]

        # Add transit days between gates
        if i < len(gates) - 1:
            next_gate = gates[i + 1]
            transit_days = gate_to_gate_df.loc[(gate_to_gate_df['Start_Gate'] == gate) & (gate_to_gate_df['End_Gate'] == next_gate), 'Transit_Days']
            if not transit_days.empty:
                total_travel_days += transit_days.iloc[0]

    # Add travel days for the end port connection
    end_port_travel_days = port_gate_df.loc[(port_gate_df['port_id'] == endport) & (port_gate_df['gate_name'] == gates[-1]), 'travel_days']
    if not end_port_travel_days.empty:
        total_travel_days += extract_last_number(end_port_travel_days.iloc[0])

    travel_days_dict[(startport, endport)] = total_travel_days
    gate_cost_dict[(startport, endport)] = total_gate_cost
    passby_gates_dict[(startport, endport)] = gates

# Define the Node class
class Node:
    def __init__(self, node_id, window_start, window_end, node_type, port):
        self.node_id = node_id
        self.window_start = window_start
        self.window_end = window_end
        self.node_type = node_type
        self.port = port

    def __repr__(self):
        return f"Node(node_id={self.node_id}, window_start={self.window_start}, window_end={self.window_end}, node_type='{self.node_type}', port={self.port})"

# Create a sample list of current network nodes
current_network_nodes = [
    Node(0, 0, 10, 'load', 0),
    Node(1, 0, 10, 'discharge', 1),
    Node(2, 0, 10, 'term_source', 2),
    Node(3, 0, 10, 'term_sink', 3)
]

# Define the get_node function
def get_node(port_id):
    for node in current_network_nodes:
        if node.port == port_id:
            return node
    return None

# Define the create_arc function
def create_arc(source_node, end_node):
    arc = {
        'source_node': source_node,
        'end_node': end_node
    }
    return arc

# Define the has_gates function
def has_gates(startport, endport):
    return (startport, endport) in passby_gates_dict

# Define the fetch_gates function
def fetch_gates(startport, endport):
    return passby_gates_dict.get((startport, endport), [])

# Define the get_original_arc_label function
def get_original_arc_label(source_node, end_node):
    # Placeholder function to fetch original arc labels
    # Replace with actual logic to fetch original labels such as vessel_id, To, From date, etc.
    return f"Original Arc: {source_node.node_id} -> {end_node.node_id}"

# Define the get_node_details function to format node details in a table
def get_node_details(node):
    details = f"""
    <table>
        <tr><th>Attribute</th><th>Value</th></tr>
        <tr><td>Node ID</td><td>{html.escape(str(node.node_id))}</td></tr>
        <tr><td>Window Start</td><td>{html.escape(str(node.window_start))}</td></tr>
        <tr><td>Window End</td><td>{html.escape(str(node.window_end))}</td></tr>
        <tr><td>Node Type</td><td>{html.escape(str(node.node_type))}</td></tr>
        <tr><td>Port</td><td>{html.escape(str(node.port))}</td></tr>
    </table>
    """
    return details

# Define the port_gate_arc_creation method
def port_gate_arc_creation(travel_days_dict, gate_cost_dict, passby_gates_dict):
    arcs = []

    for (startport, endport) in travel_days_dict.keys():
        source_node = get_node(startport)
        end_node = get_node(endport)

        if source_node and end_node:
            arc = create_arc(source_node, end_node)
            arcs.append(arc)

    return arcs

# Define the create_visual function
def create_visual(arcs, travel_days_dict, gate_cost_dict):
    net = Network(height='750px', width='100%', directed=True)
    added_arcs = set()

    # Define colors for each node type
    node_colors = {
        'load': 'blue',
        'discharge': 'purple',
        'term_source': 'green',
        'term_sink': 'red'
    }

    # Define labels for each node type
    node_labels = {
        'load': 'L',
        'discharge': 'D',
        'term_source': 'S',
        'term_sink': 'T'
    }

    # Add nodes to the network
    for arc in arcs:
        source_node = arc['source_node']
        end_node = arc['end_node']

        # Get node details in table format
        source_node_details = get_node_details(source_node)
        end_node_details = get_node_details(end_node)

        # Add source node
        net.add_node(
            source_node.node_id,
            label=node_labels[source_node.node_type],
            title=source_node_details,
            color=node_colors[source_node.node_type],
            shape='circle',
            font={'size': 20}
        )

        # Add end node
        net.add_node(
            end_node.node_id,
            label=node_labels[end_node.node_type],
            title=end_node_details,
            color=node_colors[end_node.node_type],
            shape='circle',
            font={'size': 20}
        )

        # Determine if arrows should be present based on the node type
        #arrows = None if source_node.node_type in ['term_source', 'term_sink'] else 'to'

        # Create the label for the original arc
        original_arc_label = get_original_arc_label(source_node, end_node)
        arc_key = (source_node.node_id, end_node.node_id, 'original')

        # Add the original arc if not already added
        if arc_key not in added_arcs:
            net.add_edge(source_node.node_id, end_node.node_id, label=original_arc_label, title=original_arc_label)
            added_arcs.add(arc_key)

        # Check if there are passby gates
        if has_gates(source_node.port, end_node.port):
            passby_gates = fetch_gates(source_node.port, end_node.port)
            gate_labels = ' | '.join(passby_gates)
            edge_label = f"Travel Days: {travel_days_dict[(source_node.port, end_node.port)]}, Gate Cost: {gate_cost_dict[(source_node.port, end_node.port)]} | Gates: {gate_labels}"
            arc_key_with_gates = (source_node.node_id, end_node.node_id, 'with_gates')

            # Add the arc with gates if not already added
            if arc_key_with_gates not in added_arcs:
                net.add_edge(source_node.node_id, end_node.node_id, label='', title=edge_label, color='red', dashes=True)
                added_arcs.add(arc_key_with_gates)

    # Add JavaScript for displaying node details in a custom tooltip
    net.set_options("""
    var options = {
        "nodes": {
            "shape": "dot",
            "size": 16,
            "font": {
                "size": 20,
                "vadjust": -10
            }
        },
        "edges": {
            "width": 2
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "hideEdgesOnDrag": true
        },
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
                "enabled": true,
                "iterations": 1000,
                "updateInterval": 25
            }
        }
    }
    """)

    # Add custom tooltip HTML and CSS
    net.html += """
    <style>
    .custom-tooltip {
        position: absolute;
        display: none;
        background-color: white;
        border: 1px solid black;
        padding: 10px;
        z-index: 1000;
    }
    </style>
    <div id="customTooltip" class="custom-tooltip"></div>
    <script>
    var tooltip = document.getElementById('customTooltip');
    function showTooltip(event, details) {
        tooltip.innerHTML = details;
        tooltip.style.display = 'block';
        tooltip.style.left = event.pageX + 'px';
        tooltip.style.top = event.pageY + 'px';
    }
    function hideTooltip() {
        tooltip.style.display = 'none';
    }
    </script>
    """

    # Add JavaScript to handle node hover events
    net.html += """
    <script>
    network.on('hoverNode', function(params) {
        var nodeId = params.node;
        var node = nodes.get(nodeId);
        showTooltip(params.event, node.title);
    });
    network.on('blurNode', function(params) {
        hideTooltip();
    });
    </script>
    """

    #net.show_buttons(filter_=['physics'])
    net.show('network.html',notebook=False)

# Call the port_gate_arc_creation method and output the arcs
arcs = port_gate_arc_creation(travel_days_dict, gate_cost_dict, passby_gates_dict)

# Create the visual representation of the network
create_visual(arcs, travel_days_dict, gate_cost_dict)
