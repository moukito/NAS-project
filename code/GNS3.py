import os
import telnetlib

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

    def __init__(self, project_name: str, server: str = "http://localhost:3080") -> None:
        # Initialize the Gns3 server connection and project
        self.server = gns3fy.Gns3Connector(server)
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
                self.telnet_session.read_until(b"#", timeout=10)  # Wait until prompt is ready
                self.active_node = node_name  # Set the active node name
                print(f"Telnet connection to {node_name} is now open.")
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
            with open("command_output.log", "a") as log_file:  # Open a log file in append mode
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
    def get_node(self, node_name:str) -> dict:
        """
        Returns the node of name node_name 's data, or raises an error if it doesn't exist in the project

        input:node_name : hostname of node as a string
        returns: the corresponding node dict
        raises ValueError: If the specified node is not found.
        """
        # Find the specified node in the project nodes list
        node = next((n for n in self.project.nodes if n.name == node_name), None)
        if node:
            return node # Return the node's directory
        else:
            raise ValueError(f"Node {node_name} not found in the project.")  # Raise error if node not found
    def get_used_interface_for_link(self, r1:str, r2:str):
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
                interface = link.nodes[i]["adapter_number"]
        if interface == None:
            raise KeyError(f"Link between {r1} and {r2} not found in the project.")
        else:
            return interface
if __name__ == "__main__":
    connector = Connector("projet_TP3_BGP_2")
    print(f"Project '{connector.project.name}' connection successful.")  # Confirm project connection
    print(f"Project '{connector.project.name}' has {len(connector.project.nodes)} nodes.")  # Node count
    print(f"connector.project.nodes: {connector.project.nodes}")  # Print nodes in the project
    print(f"connector.project.links: {connector.project.links}")
    print(connector.get_router_config_path("R1"))  # Config path for node R1
    print(f"{connector.get_used_interface_for_link("R1", "R2")}")

    # List of commands to execute on the node
    commands = [
        "show",  # Example command
        "show run"  # Example: Display the running configuration
    ]

    connector.telnet_connection("R1")  # Open Telnet connection
    connector.send_commands_to_node(commands)  # Send commands to the node
