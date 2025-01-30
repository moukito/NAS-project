import json

from GNS3 import Connector


class ConnectorWithNodePosition(Connector):
    """
    A class extending Connector to retrieve x and y positions of nodes in the project.
    """

    def get_node_positions(self):
        """
        Retrieves the x and y positions of all nodes in the project.
        
        :return: A dictionary where the keys are node names, and the values are dictionaries with x and y positions.
        """
        node_positions = {}

        try:
            # Iterate through each node in the project
            for node in self.project.nodes:
                node_positions[node.name] = {
                    "x": node.x,  # Default to 0 if position data is missing
                    "y": node.y  # Default to 0 if position data is missing
                }
        except Exception as e:
            print(f"Error retrieving node positions: {e}")

        return node_positions


def add_positions_to_json(full_infra, node_positions):
    """
    Add x and y coordinates from node_positions to the full_infra JSON structure.

    :param full_infra: The JSON object containing infrastructure data.
    :param node_positions: Dictionary with hostname as key and x, y positions as values.
    :return: Updated full_infra JSON.
    """
    for router in full_infra["Les_routeurs"]:
        hostname = router["hostname"]
        if hostname in node_positions:
            position = node_positions[hostname]
            router["position"] = {
                "x": position["x"],
                "y": position["y"]
            }
    return full_infra


if __name__ == "__main__":
    # Use the extended Connector class
    connector = ConnectorWithNodePosition()

    # Retrieve node positions
    node_positions = connector.get_node_positions()

    # Path to the JSON file
    json_file_path = "format/full_infra.json"

    # Read the existing JSON file
    with open(json_file_path, "r") as json_file:
        full_infra = json.load(json_file)

    # Add node positions to the JSON
    updated_full_infra = add_positions_to_json(full_infra, node_positions)

    # Save updated JSON back to the file
    with open(json_file_path, "w") as json_file:
        json.dump(updated_full_infra, json_file, indent=4)

    print("Positions added to JSON and saved successfully.")
