import ipaddress
import json

from autonomous_system import AS, GlobalRouterIDCounter
from network import SubNetwork
from router import Router
from writer import get_final_config_string

AS_LIST_NAME = "Les_AS"
ROUTER_LIST_NAME = "Les_routeurs"
IP_VERSION_KEY = "ip_version"


def router_list_into_hostname_dictionary(router_list: list[Router]) -> dict[str, Router]:
    dico = {}
    for router in router_list:
        dico[router.hostname] = router
    return dico


def as_list_into_as_number_dictionary(as_list: list[AS]) -> dict[int, AS]:
    dico = {}
    for autonomous in as_list:
        dico[autonomous.AS_number] = autonomous
    return dico


def parse_intent_file(file_path: str) -> tuple[list[AS], list[Router]]:
    """
    Fonction de parsing d'un fichier d'intention dans notre format

    entrée: file_path, un chemin relatif ou absolu valide dans le système de fichier
    sortie: tuple contenant la liste des AS, et la liste des routeurs dans le fichier donné

    Si le chemin ne mène pas à un fichier valide, la fonction va renvoyer une exception
    """
    with open(file_path, "r") as file:
        data = json.load(file)
        
        # Récupérer la version IP (par défaut IPv6 si non spécifiée)
        ip_version = data.get(IP_VERSION_KEY, 6)
        
        les_as = []
        global_counter = GlobalRouterIDCounter()
        for autonomous in data[AS_LIST_NAME]:
            as_number = autonomous["AS_number"]
            routers = autonomous["routers"]
            
            # Traitement selon la version IP
            if ip_version == 6: # todo : care
                ip = SubNetwork(ipaddress.IPv6Network(autonomous["ipv6_prefix"]), len(routers))
                ipv4_prefix = None
                # Traitement du préfixe loopback pour IPv6
                loopback_prefix = SubNetwork(ipaddress.IPv6Network(autonomous["loopback_prefix"]), len(routers))
            else:
                ip = None # SubNetwork(ipaddress.IPv6Network(autonomous.get("ipv6_prefix", "2001:db8::/64")), len(routers))
                ipv4_prefix = SubNetwork(ipaddress.IPv4Network(autonomous["ipv4_prefix"]), len(routers))
                # Traitement du préfixe loopback pour IPv4
                loopback_prefix = SubNetwork(ipaddress.IPv4Network(autonomous["ipv4_loopback_prefix"]), len(routers))
            
            internal_routing = autonomous["internal_routing"]
            
            # Gestion des AS connectés selon la version IP
            connected_as = autonomous.get("connected_AS", [])
            
            les_as.append(AS(ip, as_number, routers, internal_routing, connected_as, loopback_prefix, global_counter, ip_version, ipv4_prefix))

        les_routers = []
        for router in data[ROUTER_LIST_NAME]:
            hostname = router["hostname"]
            links = router["links"]
            as_number = router["AS_number"]
            LDP_activation = router.get("LDP_activation", False)
            position = router.get("position", {"x": 0, "y": 0})
            new_router = Router(hostname, LDP_activation, links, as_number, position, ip_version)
            
            ipv6_loopback_address = router.get("ipv6_loopback_address", None)
                
            if ipv6_loopback_address is not None:
                addr, prefix = ipv6_loopback_address.split('/')
                new_router.loopback_address = ipaddress.IPv6Address(addr)
            
            ipv4_loopback_address = router.get("ipv4_loopback_address", None)

            if ipv4_loopback_address is not None:
                addr, prefix = ipv4_loopback_address.split('/')
                new_router.router_id = int(addr.split(".")[-1])
                for one_as in les_as:
                    if one_as.AS_number == as_number:
                        one_as.global_router_counter.reserve_id(new_router.router_id)
                        new_as = one_as
                        les_as.pop(les_as.index(one_as))
                        les_as.append(new_as)

            les_routers.append(new_router)

        return les_as, les_routers
