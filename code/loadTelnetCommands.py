"""Telnet command loading module for network automation tasks.

This module provides functionality for loading Telnet commands from text files,
which can be used for network device configuration and management. It offers
a simple interface to read command files line by line, preparing them for
execution on network devices via Telnet connections.

The module is designed to work with the GNS3 automation framework and can be
used to load command sets for router configuration, testing, and management.

Typical usage example:
    commands = load_file("format/telnetCommands")
    connector.send_commands_to_node(commands, 'R1')
"""

def load_file(file: str) -> list[str]:
	"""
	Reads a text file line by line and returns a list of stripped lines.

	Args:
		file (str): Path to the file to be read.

	Returns:
		list[str]: A list of strings, where each string corresponds to a line in the file,
			stripped of leading and trailing whitespace.
	"""
	with open(file, 'r') as file:
		lines = file.readlines()
		lines_list = [line.strip() for line in lines]
	return lines_list


if __name__ == "__main__":
	"""
	Entry point of the script.
	This block demonstrates how to use the `load_file` function
	by loading and printing the contents of 'format/telnetCommands'.
	"""
	print(load_file("format/telnetCommands"))
