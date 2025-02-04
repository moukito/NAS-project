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
