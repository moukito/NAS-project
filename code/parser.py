import json
import ipaddress
import os

from autonomous_system import AS
from router import Router
from ipv6 import SubNetwork

AS_LIST_NAME = "Les_AS"
ROUTER_LIST_NAME = "Les_routeurs"

def router_list_into_hostname_dictionary(router_list:list[Router]) -> dict[str, Router]:
    dico = {}
    for router in router_list:
        dico[router.hostname] = router
    return dico

def as_list_into_as_number_dictionary(as_list:list[AS]) -> dict[int, AS]:
    dico = {}
    for autonomous in as_list:
        dico[autonomous.AS_number] = autonomous
    return dico

def parse_intent_file(file_path:str) -> tuple[list[AS], list[Router]]:
    """
    Fonction de parsing d'un fichier d'intention dans notre format

    entrée: file_path, un chemin relatif ou absolu valide dans le système de fichier
    sortie: tuple contenant la liste des AS, et la liste des routeurs dans le fichier donné

    Si le chemin ne mène pas à un fichier valide, la fonction va renvoyer une exception
    """
    with open(file_path, "r") as file:
        data = json.load(file)
        les_as = []
        for autonomous in data[AS_LIST_NAME]:
            
            as_number = autonomous["AS_number"]
            routers = autonomous["routers"]
            ip = SubNetwork(ipaddress.IPv6Network(autonomous["ipv6_prefix"]), len(routers))
            internal_routing = autonomous["internal_routing"]
            connected_as = autonomous["connected_AS"]
            les_as.append(AS(ip, as_number, routers, internal_routing, connected_as))
        les_routers = []
        for router in data[ROUTER_LIST_NAME]:
            hostname = router["hostname"]
            links = router["links"]
            as_number = router["AS_number"]
            les_routers.append(Router(hostname, links, as_number))
        return (les_as, les_routers)

(les_as, les_routeurs) = parse_intent_file("format/exemple.json")
for autonomous in les_as:
    print(autonomous)

as_dico = as_list_into_as_number_dictionary(les_as)
routeur_dico = router_list_into_hostname_dictionary(les_routeurs)

for routeur in les_routeurs:
    routeur.set_interface_configuration_data(as_dico, routeur_dico)
    print(routeur.config_str_per_link)

for routeur in les_routeurs:
    routeur.set_bgp_config_data(as_dico, routeur_dico)
    print(routeur.config_bgp)

print(hex(256))