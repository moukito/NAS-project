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

    def modify_router_config(self, node_name: str, config: str) -> None:
        """Modify the configuration of a specified router node."""
        node = next((n for n in self.project.nodes if n["name"] == node_name), None)
        if node:
            router = gns3fy.Node(name=node["name"], connector=self.server, node_id=node["node_id"])
            router.update({"properties": {"config": config}})
        else:
            raise ValueError(f"Node {node_name} not found in the project.")
