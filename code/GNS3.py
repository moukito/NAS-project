import os
import telnetlib
import time

import gns3fy


class Connector:
	"""
	Connector class to interact with a GNS3 project, manage nodes, and send commands
	via Telnet sessions.
	"""

	def __init__(self, project_name: str = None, server: str = "http://localhost:3080") -> None:
		"""
		Initializes a connection to a GNS3 server and loads a project.

		Args:
			project_name (str): The name of the GNS3 project to load. If None, it selects the
								first opened project automatically.
			server (str): The GNS3 server URL (default: "http://localhost:3080").
		"""
		self.server = gns3fy.Gns3Connector(server)
		if project_name is None:
			for project in self.server.get_projects():
				if project["status"] == "opened":
					project_name = project["name"]
					break
		self.project = gns3fy.Project(project_name, connector=self.server)
		self.project.get()
		self.telnet_session = {}

	def get_router_config_path(self, node_name: str) -> str:
		"""
		Retrieves the path to the startup configuration file for a given router.

		Args:
			node_name (str): Name of the router/node.

		Returns:
			str: Path to the router's startup configuration file.

		Raises:
			FileNotFoundError: If the configuration directory or file does not exist.
			ValueError: If the specified node is not found in the project.
		"""
		node = next((n for n in self.project.nodes if n.name == node_name), None)
		if node:
			path = os.path.join(node.node_directory, "configs")
			if not os.path.isdir(path):
				raise FileNotFoundError(f"The configs directory does not exist at {path}")

			for root, _, files in os.walk(path):
				for file in files:
					if "startup-config.cfg" in file:
						return os.path.join(root, file)

			raise FileNotFoundError(f"No startup-config file found in {path}")
		else:
			raise ValueError(f"Node {node_name} not found in the project.")

	def telnet_connection(self, node_name: str) -> None:
		"""
		Establishes a Telnet connection to a given router/node.

		Args:
			node_name (str): Name of the router/node.

		Raises:
			ValueError: If the node does not support Telnet or does not exist.
			ConnectionError: If the connection fails.
			TimeoutError: If the router does not become ready within the expected time.
		"""
		node = next((n for n in self.project.nodes if n.name == node_name), None)

		if node:
			if node.console_type != "telnet":
				raise ValueError(f"Node {node_name} does not support Telnet.")

			host = "localhost"
			port = node.console

			print(f"Connecting to {node_name} on {host}:{port} via Telnet...")

			try:
				self.telnet_session[node_name] = telnetlib.Telnet(host, port)
				node_name = node_name

				print("Telnet connection established. Waiting for router to be ready...")

				max_attempts = 30
				attempt = 0
				while attempt < max_attempts:
					try:
						self.telnet_session[node_name].write(b"\r\n")
						output = self.telnet_session[node_name].read_very_eager().decode('ascii')
						if f"{node_name}#" in output:
							print(f"Router {node_name} is ready.")
							self.telnet_session[node_name].write(b"\r\n")
							time.sleep(1)
							self.telnet_session[node_name].read_until(f"{node_name}#".encode('ascii'))
							return
					except Exception as e:
						pass
					time.sleep(3)
					attempt += 1
				raise TimeoutError(f"Router {node_name} did not become ready within {max_attempts * 3} seconds.")

			except Exception as e:
				self.telnet_session[node_name] = None
				node_name = None
				raise ConnectionError(f"Failed to connect to {node_name}: {e}")
		else:
			raise ValueError(f"Node {node_name} not found in the project.")

	def send_commands_to_node(self, commands: list, node_name) -> None:
		"""
		Sends a list of commands to a router via an active Telnet connection.

		Args:
			commands (list): List of commands to send to the router.
			node_name (str): Name of the router/node.

		Raises:
			RuntimeError: If there is no active Telnet connection or if the
				command execution fails.
		"""
		if self.telnet_session.get(node_name, None) is None:
			raise RuntimeError("No active Telnet connection. Please establish a connection using telnet_connection().")

		log_path = f"command_output_{node_name}.log"
		try:
			with open(log_path, "w") as log_file:
				for command in commands:
					print(f"Sending command: {command}")
					self.telnet_session[node_name].write(command.encode('ascii') + b"\r\n")

					output = b""

					chunk = self.telnet_session[node_name].read_until(f"#".encode('ascii'), timeout=2)
					output += chunk

					while b"--More--" in chunk:
						self.telnet_session[node_name].write(b" ")
						chunk = self.telnet_session[node_name].read_until(b"--More--", timeout=2)
						output += chunk

					decoded_output = output.decode('ascii').replace(f"{node_name}#", "").replace(f"{node_name}(config)#", "").replace(f"{node_name}(config-rtr)#", "").replace(f"{node_name}(config-router)#", "").replace(f"{node_name}(config-router-af)#", "").replace(f"{node_name}(config-route-map)#", "").replace(f"{node_name}(config-if)#", "").replace(command, "").strip()
					log_file.write(f"Command: {command}\n{decoded_output}\n\n")
			self.clean_log(log_path, log_path)
		except Exception as e:
			raise RuntimeError(f"Failed to send commands to {node_name}: {e}")

	def close_telnet_connection(self, node_name: str) -> None:
		"""
		Closes the Telnet connection to a specified router/node.

		Args:
			node_name (str): Name of the router/node.

		Raises:
			Exception: If closing the connection fails.
		"""
		if self.telnet_session[node_name]:
			try:
				self.telnet_session[node_name].write(b"\r\n")
				self.telnet_session[node_name].close()
				print(f"Telnet connection to {node_name} has been closed.")
			except Exception as e:
				print(f"Error closing Telnet connection: {e}")
			finally:
				self.telnet_session[node_name] = None
		else:
			print("No active Telnet connection to close.")

	def __del__(self):
		"""
		Destructor function to close all Telnet connections automatically
		when the Connector object is deleted.
		"""
		for node_name, session in self.telnet_session.items():
			if session:
				print("Automatically closing Telnet connection...")
				self.close_telnet_connection(node_name)

	@staticmethod
	def refresh_project(func):
		"""
		Decorator to refresh the project state before and after calling a method.

		Args:
			func: The method to decorate.

		Returns:
			A wrapped function that refreshes the project state after execution.
		"""

		def wrapper(self, *args, **kwargs):
			result = func(self, *args, **kwargs)
			self.project.get()
			return result

		return wrapper

	def get_node(self, node_name: str) -> gns3fy.Node:
		"""
		Retrieves a node object from the current GNS3 project.

		Args:
			node_name (str): Name of the node to retrieve.

		Returns:
			gns3fy.Node: The retrieved node object.

		Raises:
			ValueError: If the node does not exist in the project.
		"""
		node = next((n for n in self.project.nodes if n.name == node_name), None)
		if node:
			return node
		else:
			raise ValueError(f"Node {node_name} not found in the project.")

	@refresh_project
	def create_node(self, node_name: str, template: str) -> None:
		"""
		Creates a new node in the GNS3 project.

		Args:
			node_name (str): Name of the new node.
			template (str): Template for the node.
		"""
		node = gns3fy.Node(
			project_id=self.project.project_id,
			connector=self.server,
			name=node_name,
			template=template
		)
		node.create()

	def get_used_interface_for_link(self, r1: str, r2: str) -> int:
		"""
		Identifies the interface used for the link between two nodes.

		Args:
			r1 (str): Name of the first node (router).
			r2 (str): Name of the second node (router).

		Returns:
			int: The interface number used by the first node in the link.

		Raises:
			KeyError: If no link exists between the specified nodes in the project.
		"""
		node_1 = self.get_node(r1)
		node_2 = self.get_node(r2)
		interface = None
		for link in self.project.links:
			found = 0
			node_1_index = None
			for (i, node) in enumerate(link.nodes):
				if node["node_id"] == node_1.node_id:
					node_1_index = i
					found += 1
				if node["node_id"] == node_2.node_id:
					found += 1
			if found == 2:
				interface = link.nodes[node_1_index]["adapter_number"]
		if interface == None:
			raise KeyError(f"Link between {r1} and {r2} not found in the project.")
		else:
			return interface

	@refresh_project
	def create_link_if_it_doesnt_exist(self, r1: str, r2: str, interface_1: int, interface_2: int) -> None:
		"""
		Creates a link between two routers if it does not already exist.

		Args:
			r1 (str): Name of the first router.
			r2 (str): Name of the second router.
			interface_1 (int): Interface adapter number for the first router.
			interface_2 (int): Interface adapter number for the second router.

		Raises:
			ValueError: If the specified interfaces are already in use.
			Exception: If an error occurs while creating the link.
		"""
		try:
			node_1 = self.get_node(r1)
			node_2 = self.get_node(r2)
			interface_1_real = None
			interface_2_real = None
			already_found = False
			for link in self.project.links:
				found = 0
				node_1_index = None
				node_2_index = None
				for (i, node) in enumerate(link.nodes):
					if node["node_id"] == node_1.node_id:
						node_1_index = i
						found += 1
					if node["node_id"] == node_2.node_id:
						node_2_index = i
						found += 1
				if found == 2:
					interface_1_real = link.nodes[node_1_index]["adapter_number"]
					interface_2_real = link.nodes[node_2_index]["adapter_number"]
					already_found = True
			if interface_1_real == interface_1 or already_found:
				if interface_2_real == interface_2 or already_found:
					pass
				else:
					raise ValueError(f"Interface {interface_1} already in use")
			else:
				if interface_2_real == interface_2:
					raise ValueError(f"Interface {interface_2} already in use")
				else:
					nodes = [
						{"node_id": node_1.node_id, "adapter_number": interface_1, "port_number": 0},
						{"node_id": node_2.node_id, "adapter_number": interface_2, "port_number": 0}
					]
					link = gns3fy.Link(project_id=self.project.project_id, connector=self.server, nodes=nodes)
					link.create()

		except Exception as exce:
			print("Had an issue creating links : ", exce)

	@refresh_project
	def update_node_position(self, node_name: str, x: int, y: int) -> None:
		"""
		Updates the position of a specified node in the GNS3 project.

		Args:
			node_name (str): Name of the node to update.
			x (int): New X-coordinate for the node.
			y (int): New Y-coordinate for the node.

		Raises:
			RuntimeError: If updating the position fails for any reason.
		"""
		try:
			node = self.get_node(node_name)
			node.update(x=x, y=y)
		except Exception as e:
			raise RuntimeError(f"Failed to update position for node '{node_name}': {e}")

	@refresh_project
	def start_node(self, node_name: str) -> None:
		"""
		Stops and then starts the specified node (reboots it).

		Args:
			node_name (str): Name of the node to start.

		Raises:
			Exception: If the node cannot be stopped or started.
		"""
		node = self.get_node(node_name)
		node.stop()
		node.start()

	@staticmethod
	def clean_log(input_file: str, output_file: str) -> None:
		"""
		Cleans up a log file by removing empty/unused lines and specific markers like `--More--`.

		Args:
			input_file (str): Path to the input log file.
			output_file (str): Path where the cleaned-up log file will be saved.

		Raises:
			FileNotFoundError: If the input file does not exist.
			Exception: If any other error occurs during log cleanup.

		Notes:
			This function removes markers like `--More--` and ensures the output
			file contains neatly formatted command outputs.
		"""
		try:
			with open(input_file, "r") as log_file:
				lines = log_file.readlines()

			cleaned_lines = []
			for line in lines:
				if "--More--" in line:
					continue
				stripped_line = line.rstrip()
				if stripped_line:
					if len(cleaned_lines) == 0:
						cleaned_lines.append(stripped_line + "\n")
					elif stripped_line.startswith("Command: "):
						cleaned_lines.append("\n" + stripped_line + "\n")
					else:
						cleaned_lines.append(stripped_line)

			with open(output_file, "w") as cleaned_log:
				cleaned_log.write("\n".join(cleaned_lines))

			print(f"Log successfully cleaned. Output saved to {output_file}.")

		except FileNotFoundError as err:
			print(f"Error: File not found - {err}")
		except Exception as err:
			print(f"An error occurred: {err}")

	def send_command_and_get_output(self, command: str, node_name: str) -> str:
		"""
		Envoie une commande à un routeur via une connexion Telnet active et retourne la sortie.

		Args:
			command (str): Commande à envoyer au routeur.
			node_name (str): Nom du routeur/nœud.

		Returns:
			str: La sortie de la commande.

		Raises:
			RuntimeError: Si aucune connexion Telnet active n'existe ou si l'exécution
						  de la commande échoue.
		"""
		if self.telnet_session.get(node_name, None) is None:
			raise RuntimeError("No active Telnet connection. Please establish a connection using telnet_connection().")

		try:
			self.telnet_session[node_name].write(command.encode('ascii') + b"\r\n")

			output = b""

			chunk = self.telnet_session[node_name].read_until(f"#".encode('ascii'), timeout=2)
			output += chunk

			# Handle "More" prompts for paginated output
			while b"--More--" in chunk:
				self.telnet_session[node_name].write(b" ")
				chunk = self.telnet_session[node_name].read_until(b"--More--", timeout=2)
				output += chunk

			decoded_output = output.decode('ascii')
			# Clean up the output by removing the command prompt and the command itself
			cleaned_output = decoded_output.replace(f"{node_name}#", "")
			cleaned_output = cleaned_output.replace(f"{node_name}(config)#", "")
			cleaned_output = cleaned_output.replace(f"{node_name}(config-rtr)#", "")
			cleaned_output = cleaned_output.replace(f"{node_name}(config-router)#", "")
			cleaned_output = cleaned_output.replace(f"{node_name}(config-router-af)#", "")
			cleaned_output = cleaned_output.replace(f"{node_name}(config-route-map)#", "")
			cleaned_output = cleaned_output.replace(f"{node_name}(config-if)#", "")
			cleaned_output = cleaned_output.replace(command, "").strip()

			return cleaned_output

		except Exception as e:
			raise RuntimeError(f"Failed to send command to {node_name}: {e}")


if __name__ == "__main__":
	connector = Connector()
	print(f"Project '{connector.project.name}' connection successful.")
	print(f"Project '{connector.project.name}' has {len(connector.project.nodes)} nodes.")
	print(f"connector.project.nodes: {connector.project.nodes}")
	print(f"connector.project.links: {connector.project.links}")
	print(connector.get_router_config_path('R1'))
	print(f"{connector.get_used_interface_for_link('R1', 'R2')}")

	connector.start_node('R1')
	commands = ["show", "show run"]

	connector.telnet_connection('R1')
	connector.send_commands_to_node(commands, 'R1')
	connector.close_telnet_connection('R1')
