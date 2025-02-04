import json

from GNS3 import Connector


class ConnectorWithNodePosition(Connector):
	"""
	A subclass of the GNS3 Connector class that adds functionality to
	retrieve node positions (x and y coordinates) from a GNS3 project.
	"""

	def get_node_positions(self):
		"""
		Retrieves the positions of nodes in the GNS3 project currently loaded.

		Returns:
			dict: A dictionary where each key is a node name and its value is
				  another dictionary containing the "x" and "y" coordinates.
				  Example:
				  {
					  "Node1": {"x": 100, "y": 200},
					  "Node2": {"x": 300, "y": 400}
				  }
		"""
		node_positions = {}

		try:
			for node in self.project.nodes:
				node_positions[node.name] = {
					"x": node.x,
					"y": node.y
				}
		except Exception as e:
			print(f"Error retrieving node positions: {e}")

		return node_positions


def add_positions_to_json(full_infra: dict, node_positions: dict) -> dict:
	"""
	Adds node position information to a JSON dictionary that represents
	the network infrastructure.

	Args:
		full_infra (dict): The existing JSON-like dictionary representing
						   the network infrastructure (input).
						   Should include a key `"Les_routeurs"` which is
						   a list of routers.
		node_positions (dict): A dictionary mapping node names to their
							   x and y coordinates. Example:
							   {
								   "Node1": {"x": 100, "y": 200}
							   }

	Returns:
		dict: The updated `full_infra` dictionary, with each router in
			  `"Les_routeurs"` having an additional key `"position"` containing
			  its coordinates.
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
	"""
	Main script execution:
	- Connects to the GNS3 project using the `ConnectorWithNodePosition` class.
	- Retrieves node positions (x, y) for all nodes in the project.
	- Reads a JSON file representing the network infrastructure.
	- Updates the JSON with the node position data.
	- Saves the updated JSON back to the same file.
	"""
	connector = ConnectorWithNodePosition()

	node_positions = connector.get_node_positions()

	json_file_path = "format/full_infra.json"

	with open(json_file_path, "r") as json_file:
		full_infra = json.load(json_file)

	updated_full_infra = add_positions_to_json(full_infra, node_positions)

	with open(json_file_path, "w") as json_file:
		json.dump(updated_full_infra, json_file, indent=4)

	print("Positions added to JSON and saved successfully.")
