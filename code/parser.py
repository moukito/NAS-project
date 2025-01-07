import json
import ipaddress

from autonomous_system import AS
from router import Router

AS_LIST_NAME = "Les_AS"
ROUTER_LIST_NAME = "Les_routers"

def parse_intent_file(file_path:str) -> tuple[list[AS], list[Router]]:
    with open(file_path, "r") as file:
        data = json.load(file)
        les_as = []
        for autonomous in data[AS_LIST_NAME]:
            ip = ipaddress.IPv6Network(autonomous["ipv6_prefix"])
            as_number = autonomous["AS_number"]
            routers = autonomous["routers"]
            routage_interne = autonomous["routage_interne"],
            connected_as = autonomous["AS_connectes"]
            les_as.append(AS())
    return ("", "")