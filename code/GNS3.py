import gns3fy


class Connector:
    """
    Provides functionality to interact with a GNS3 project and modify router configurations.

    This class allows connecting to a GNS3 server, managing a project, and modifying
    configurations of specific nodes within the project.

    Type: str server: The GNS3 server connection instance.
    Type: str project: The GNS3 project instance associated with the server connection.
    """

    def __init__(self, project_name: str, server: str = "http://localhost:3080") -> None:
        self.server = gns3fy.Gns3Connector(server)
        self.project = gns3fy.Project(project_name, connector=self.server)

    def get_router_config_path(self, node_name: str) -> str:
        """
        Get the path to the configuration file of a specified node.

        :param node_name: Name of the node to retrieve the config file path.
        :return: The path to the config file if the node exists.
        :raises ValueError: If the specified node is not found.
        """
        node = next((n for n in self.project.nodes if n.name == node_name), None)
        if node:
            return node.node_directory
        else:
            raise ValueError(f"Node {node_name} not found in the project.")


if __name__ == "__main__":
    connector = Connector("nap")
    connector.project.get()
    print(f"Project '{connector.project.name}' connection successful.")
    print(f"Project '{connector.project.name}' has {len(connector.project.nodes)} nodes.")
    print(f"connector.project.nodes: {connector.project.nodes}")
    print(connector.get_router_config_path("R1") + "\\configs\\i1_startup-config.cfg")
