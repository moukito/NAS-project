def write_string_to_file(file_path, data):
    """
    Writes the given string to a file at the specified path.

    Parameters:
    - file_path (str): The path to the file where the string will be written.
    - data (str): The string to write into the file.

    Exceptions:
    Raises IOError if the file cannot be written.
    """
    try:
        with open(file_path, 'w') as file:
            file.write(data)
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")
