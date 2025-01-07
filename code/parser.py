import json

from autonomous_system import AS
from router import Router

AS_LIST_NAME = "Les_AS"
ROUTER_LIST_NAME = "Les_routers"

def parse_intent_file(file_path:str) -> tuple[list[AS], list[Router]]:
    with open(file_path, "r") as file:
        data = json.load(file)
        les_as = []
        for as in data["Les"]
    return ("", "")