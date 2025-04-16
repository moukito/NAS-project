"""
Intent parser module for network configuration.

This module provides tools for parsing network intent files and converting them into
network configuration objects. It handles both IPv4 and IPv6 network configurations,
creating Autonomous Systems (AS) and routers based on the specifications in the intent file.

The module supports:
- Parsing JSON intent files with network specifications
- Creating AS and router objects with appropriate configurations
- Handling both IPv4 and IPv6 addressing schemes
- Managing router IDs and loopback addresses
"""

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
    """
    Convert a list of Router objects into a dictionary indexed by hostname.
    
    Args:
        router_list: A list of Router objects
        
    Returns:
        dict[str, Router]: A dictionary mapping hostnames to Router objects
    """
    dico = {}
    for router in router_list:
        dico[router.hostname] = router
    return dico


def as_list_into_as_number_dictionary(as_list: list[AS]) -> dict[int, AS]:
    """
    Convert a list of AS objects into a dictionary indexed by AS number.
    
    Args:
        as_list: A list of AS (Autonomous System) objects
        
    Returns:
        dict[int, AS]: A dictionary mapping AS numbers to AS objects
    """
    dico = {}
    for autonomous in as_list:
        dico[autonomous.AS_number] = autonomous
    return dico


def parse_intent_file(file_path: str) -> tuple[list[AS], list[Router]]:
    """
    Parse a network intent file in JSON format.
    
    This function reads a JSON file containing network intent specifications and
    creates the corresponding AS and Router objects. It handles both IPv4 and IPv6
    network configurations.
    
    Args:
        file_path: A valid relative or absolute path to the intent file
        
    Returns:
        tuple[list[AS], list[Router]]: A tuple containing the list of AS objects
        and the list of Router objects defined in the intent file
        
    Raises:
        FileNotFoundError: If the file path is invalid
        json.JSONDecodeError: If the file contains invalid JSON
        KeyError: If required keys are missing in the JSON structure
    """
    with open(file_path, "r") as file:
        data = json.load(file)
        
        ip_version = data.get(IP_VERSION_KEY, 6)
        
        les_as = []
        global_counter = GlobalRouterIDCounter()
        for autonomous in data[AS_LIST_NAME]:
            as_number = autonomous["AS_number"]
            routers = autonomous["routers"]
            LDP_activation = autonomous.get("LDP_activation", False)
            
            if ip_version == 6:
                ip = SubNetwork(ipaddress.IPv6Network(autonomous["ipv6_prefix"]), len(routers))
                ipv4_prefix = None
                loopback_prefix = SubNetwork(ipaddress.IPv6Network(autonomous["loopback_prefix"]), len(routers))
            else:
                ip = None # SubNetwork(ipaddress.IPv6Network(autonomous.get("ipv6_prefix", "2001:db8::/64")), len(routers))
                ipv4_prefix = SubNetwork(ipaddress.IPv4Network(autonomous["ipv4_prefix"]), len(routers))
                loopback_prefix = SubNetwork(ipaddress.IPv4Network(autonomous["ipv4_loopback_prefix"]), len(routers))
            
            internal_routing = autonomous["internal_routing"]
            
            connected_as = autonomous.get("connected_AS", [])
            
            les_as.append(AS(ip, as_number, routers, internal_routing, connected_as, loopback_prefix, global_counter, ip_version, ipv4_prefix, LDP_activation))

        les_routers = []
        for router in data[ROUTER_LIST_NAME]:
            hostname = router["hostname"]
            links = router["links"]
            as_number = router["AS_number"]
            VPN_family = router.get("VPN_family", None)
            position = router.get("position", {"x": 0, "y": 0})
            new_router = Router(hostname, links, as_number, position, ip_version, VPN_family)
            
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
