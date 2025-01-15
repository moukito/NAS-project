def load_file(file):
    with open(file, 'r') as file:
        lines = file.readlines()
        lines_list = [line.strip() for line in lines]
    return lines_list


if __name__ == "__main__":
    print(loadFile("format/telnetCommands"))
