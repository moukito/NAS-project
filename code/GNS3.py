import os
import telnetlib
import time

import gns3fy


class Connector:
	"""
	A Connector class for managing Gns3 connections and interacting with network nodes.

	The Connector class is designed to interface with a Gns3 server, manage projects,
	connect to nodes via Telnet, and execute commands on those nodes. It provides
	methods for retrieving node configuration paths, establishing Telnet sessions,
	sending commands, and closing connections.

	:ivar server: Connection object to the Gns3 server.
	:type server: Gns3Connector
	:ivar project: Representation of the Gns3 project to interact with.
	:type project: Project
	:ivar telnet_session: Active Telnet session object to a network node.
	:type telnet_session: Telnet | None
	:ivar active_node: Name of the currently connected network node.
	:type active_node: str | None
	"""

	def __init__(self, project_name: str = None, server: str = "http://localhost:3080") -> None:
		# Initialize the Gns3 server connection and project
		self.server = gns3fy.Gns3Connector(server)
		if project_name is None:
			for project in self.server.get_projects():
				if project["status"] == "opened":
					project_name = project["name"]
					break
		self.project = gns3fy.Project(project_name, connector=self.server)
		self.project.get()  # Load project details
		self.telnet_session = None  # Placeholder for Telnet session
		self.active_node = None  # Currently active node

	def get_router_config_path(self, node_name: str) -> str:
		"""
		Get the path to the configuration file of a specified node.

		:param node_name: Name of the node to retrieve the config file path.
		:return: The path to the config file if the node exists.
		:raises ValueError: If the specified node is not found.
		"""
		# Find the specified node in the project nodes list
		node = next((n for n in self.project.nodes if n.name == node_name), None)
		if node:
			path = os.path.join(node.node_directory, "configs")
			# Check if the config path exists
			if not os.path.isdir(path):
				raise FileNotFoundError(f"The configs directory does not exist at {path}")

			# Search for the file containing 'startup-config'
			for root, _, files in os.walk(path):
				for file in files:
					if "startup-config.cfg" in file:
						# Return the full file path if found
						return os.path.join(root, file)  # Return the node's directory

			# Raise an exception if no matching file is found
			raise FileNotFoundError(f"No startup-config file found in {path}")
		else:
			raise ValueError(f"Node {node_name} not found in the project.")  # Raise error if node not found

	def telnet_connection(self, node_name: str) -> None:
		"""
		Opens a Telnet connection to the specified node and keeps it open.

		:param node_name: Name of the node to connect to.
		"""
		# Find the specified node in the project nodes list
		node = next((n for n in self.project.nodes if n.name == node_name), None)

		if node:
			if node.console_type != "telnet":  # Ensure the node supports Telnet
				raise ValueError(f"Node {node_name} does not support Telnet.")

			host = "localhost"
			port = node.console  # Get the console port for Telnet

			print(f"Connecting to {node_name} on {host}:{port} via Telnet...")

			try:
				# Establish Telnet connection to the node
				self.telnet_session = telnetlib.Telnet(host, port)
				self.active_node = node_name  # Set the active node name

				print("Telnet connection established. Waiting for router to be ready...")

				# Wait for the prompt indicating the router is ready
				max_attempts = 30  # Timeout after 30 seconds
				attempt = 0
				while attempt < max_attempts:
					try:
						self.telnet_session.write(b"\r\n")
						output = self.telnet_session.read_very_eager().decode('ascii')
						if f"{self.active_node}#" in output:
							print(f"Router {node_name} is ready.")
							self.telnet_session.read_until(f"{self.active_node}#".encode('ascii'))
							return  # Router is ready, exit the waiting loop
					except Exception as e:
						pass
					time.sleep(1)
					attempt += 1
				raise TimeoutError(f"Router {node_name} did not become ready within {max_attempts} seconds.")

			except Exception as e:
				# Reset on failure and raise a connection error
				self.telnet_session = None
				self.active_node = None
				raise ConnectionError(f"Failed to connect to {node_name}: {e}")
		else:
			raise ValueError(f"Node {node_name} not found in the project.")  # Raise error if node not found

	def send_commands_to_node(self, commands: list) -> None:
		"""
		Sends commands one at a time to the open Telnet connection, supporting Cisco's "More" prompt.

		:param commands: A list of strings, each representing a command to send.
		:raises RuntimeError: If no Telnet session is active.
		"""
		if self.telnet_session is None or self.active_node is None:
			# Ensure a Telnet session is active
			raise RuntimeError("No active Telnet connection. Please establish a connection using telnet_connection().")

		try:
			with open("command_output.log", "w") as log_file:  # Open a log file in append mode
				for command in commands:
					self.telnet_session.read_very_eager()  # Clear any unread output

					print(f"Sending command: {command}")
					self.telnet_session.write(command.encode('ascii') + b"\r\n")  # Send the command

					output = b""  # Aggregate command output

					# Read output until prompt is back
					chunk = self.telnet_session.read_until(f"{self.active_node}#".encode('ascii'), timeout=2)
					output += chunk

					while b"--More--" in chunk:  # Handle "More" prompts in output
						self.telnet_session.write(b" ")  # Send space for "More"
						chunk = self.telnet_session.read_until(b"--More--", timeout=2)
						output += chunk

					# Decode output and clean it from command and prompt
					decoded_output = output.decode('ascii').replace(f"{self.active_node}#", "").replace(command,
					                                                                                    "").strip()
					log_file.write(f"Command: {command}\n{decoded_output}\n\n")  # Write to log file
			self.clean_log("command_output.log", "command_output.log")
		except Exception as e:
			# Catch and raise errors during command execution
			raise RuntimeError(f"Failed to send commands to {self.active_node}: {e}")

	def close_telnet_connection(self) -> None:
		"""
		Closes the active Telnet connection gracefully.
		"""
		if self.telnet_session:
			try:
				# Gracefully close the Telnet connection
				self.telnet_session.write(b"\r\n")
				self.telnet_session.close()
				print(f"Telnet connection to {self.active_node} has been closed.")
			except Exception as e:
				# Log error during closure
				print(f"Error closing Telnet connection: {e}")
			finally:
				self.telnet_session = None  # Reset Telnet session
				self.active_node = None  # Reset active node
		else:
			print("No active Telnet connection to close.")  # No action needed if no active session

	def __del__(self):
		"""Automatically closes Telnet connection if not closed by the user."""
		if self.telnet_session:
			# Warn user and close Telnet connection on object deletion
			print("Automatically closing Telnet connection...")
			self.close_telnet_connection()

	@staticmethod
	def refresh_project(func):
		"""
		A decorator to call `self.project.get()` after the execution of the decorated function.
		"""

		def wrapper(self, *args, **kwargs):
			# Execute the original function
			result = func(self, *args, **kwargs)
			# Refresh the project state
			self.project.get()
			return result

		return wrapper

	def get_node(self, node_name: str) -> gns3fy.Node:
		"""
		Returns the node of name node_name 's data, or raises an error if it doesn't exist in the project

		input:node_name : hostname of node as a string
		returns: the corresponding node dict
		raises ValueError: If the specified node is not found.
		"""
		# Find the specified node in the project nodes list
		node = next((n for n in self.project.nodes if n.name == node_name), None)
		if node:
			return node  # Return the node's directory
		else:
			raise ValueError(f"Node {node_name} not found in the project.")  # Raise error if node not found

	@refresh_project
	def create_node(self, node_name: str, template: str):
		"""
		Creates a node with the given name and template in the project

		input : node_name, the name of the node (equivalent to the hostname for a router !) and the template name (for example, "c7200" for the routers we use)
		output : creates the node in the GNS project, will raise an error if the node already exists
		"""
		node = gns3fy.Node(
			project_id=self.project.project_id,
			connector=self.server,
			name=node_name,
			template=template
		)
		node.create()

	def get_used_interface_for_link(self, r1: str, r2: str):
		"""
		Returns the interface used for a link FROM r1 TO r2 (must be used the other way to get both ways)

		input: r1 and r2, hostname strings
		returns: name of interface (assumed to be of shape GigabitEtherneti/0) or None if the link doesn't exist in the GNS3 project
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
	def create_link_if_it_doesnt_exist(self, r1: str, r2: str, interface_1: int, interface_2: int):
		"""
		Creates the link between r1 and r2 using the given interface if it doesn't exist

		input : r1 and r2, hostname strings of the 2 routers, interface_1 the index in the standard interfaces of router r1 and interface_2 the same for r2
		returns : nothing
		raises : ValueError if the interfaces needed are already either in use
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
					# nodes[0].pop("__pydantic_initialised__")
					# nodes[1].pop("__pydantic_initialised__")
					link = gns3fy.Link(project_id=self.project.project_id, connector=self.server, nodes=nodes)
					link.create()

		except Exception as exce:
			print("Had an issue creating links : ", exce)

	@refresh_project
	def update_node_position(self, node_name: str, x: int, y: int):
		try:
			node = self.get_node(node_name)
			node.update(x=x, y=y)
		except Exception as e:
			raise RuntimeError(f"Failed to update position for node '{node_name}': {e}")

	@refresh_project
	def start_node(self, node_name: str):
		node = self.get_node(node_name)
		node.stop()
		node.start()

	@staticmethod
	def clean_log(input_file: str, output_file: str) -> None:
		"""
		Clean a log file by removing '--More--' lines and extra newlines.

		:param input_file: Path to the input log file.
		:param output_file: Path to the cleaned log file to be created.
		"""
		try:
			with open(input_file, "r") as log_file:
				lines = log_file.readlines()

			cleaned_lines = []
			for line in lines:
				# Remove lines containing "--More--" and adjacent spaces
				if "--More--" in line:
					continue
				# Strip extra spaces and preserve the line
				stripped_line = line.rstrip()
				if stripped_line:  # Ignore empty lines
					if len(cleaned_lines) == 0:
						cleaned_lines.append(stripped_line + "\n")
					elif stripped_line.startswith("Command: "):
						cleaned_lines.append("\n" + stripped_line + "\n")
					else:
						cleaned_lines.append(stripped_line)

			# Write the cleaned content into the output file
			with open(output_file, "w") as cleaned_log:
				cleaned_log.write("\n".join(cleaned_lines))

			print(f"Log successfully cleaned. Output saved to {output_file}.")

		except FileNotFoundError as err:
			print(f"Error: File not found - {err}")
		except Exception as err:
			print(f"An error occurred: {err}")


if __name__ == "__main__":
	connector = Connector()
	print(f"Project '{connector.project.name}' connection successful.")  # Confirm project connection
	print(f"Project '{connector.project.name}' has {len(connector.project.nodes)} nodes.")  # Node count
	print(f"connector.project.nodes: {connector.project.nodes}")  # Print nodes in the project
	print(f"connector.project.links: {connector.project.links}")
	print(connector.get_router_config_path("R1"))  # Config path for node R1
	# print(f"{connector.get_used_interface_for_link("R1", "R2")}")

	connector.start_node("R1")
	# List of commands to execute on the node
	commands = [
		"show",  # Example command
		"show run"  # Example: Display the running configuration
	]

	connector.telnet_connection("R1")  # Open Telnet connection
	connector.send_commands_to_node(commands)  # Send commands to the node
	connector.close_telnet_connection()
