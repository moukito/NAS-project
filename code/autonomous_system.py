"""
Module for defining and managing Autonomous Systems (AS) in network simulations.
This module contains classes to handle router ID assignment and AS configuration.
"""
from network import SubNetwork


class GlobalRouterIDCounter:
    """
    A counter class that manages and assigns unique router IDs.

    This class keeps track of used router IDs and provides methods to get
    the next available ID or reserve specific IDs.
    """
    def __init__(self):
        """
        Initialize a new router ID counter starting at 1.
        """
        self.number = 1
        self.reserved_id = []

    def get_next_router_id(self) -> int:
        """
        Get the next available router ID.

        Returns:
            int: A unique router ID that hasn't been used or reserved.
        """
        temp = self.number
        self.number += 1
        for this_id in self.reserved_id:
            if self.number == this_id:
                self.number += 1
        return temp

    def reserve_id(self, this_id: int):
        """
        Reserve a specific router ID to prevent it from being assigned.

        Args:
            this_id (int): The router ID to reserve.
        """
        self.reserved_id.append(this_id)


class AS:
    """
    Represents an Autonomous System in a network.

    An Autonomous System is a collection of connected routers that operate
    under a single administrative domain with defined routing policies.
    """
    def __init__(self, ipv6_prefix: SubNetwork | None, AS_number: int, routers: list["Router"], internal_routing: str, connected_AS: list[tuple[int, str, dict]], loopback_prefix: SubNetwork, counter:GlobalRouterIDCounter, ip_version: int = 6, ipv4_prefix: SubNetwork | None = None, LDP_activation = False):
        """
        Initialize a new Autonomous System.

        Args:
            ipv6_prefix (SubNetwork | None): The IPv6 address prefix for this AS.
            AS_number (int): The autonomous system number.
            routers (list[Router]): List of routers in this AS.
            internal_routing (str): The internal routing protocol used within this AS.
            connected_AS (list[tuple[int, str, dict]]): List of connected autonomous systems
                with their relationships (peer, provider, client) and transport information.
            loopback_prefix (SubNetwork): The prefix used for loopback addresses.
            counter (GlobalRouterIDCounter): Counter for router ID assignment.
            ip_version (int, optional): IP version used (default is 6).
            ipv4_prefix (SubNetwork | None, optional): The IPv4 address prefix for this AS.
            LDP_activation (bool, optional): Whether Label Distribution Protocol is activated.
        """
        self.subnet_counter = 0
        self.reserved_ipv4address = []
        self.ip_version = ip_version # todo : replace name with ipv6
        self.ipv6_prefix = ipv6_prefix
        self.ipv4_prefix = ipv4_prefix
        self.AS_number = AS_number
        self.routers = routers
        self.internal_routing = internal_routing
        self.connected_AS = connected_AS
        self.full_community_lists = "".join([f"ip community-list standard AS{as_num} permit {as_num}:1000\n" for (as_num, _, _) in connected_AS])
        total_not_client = 0
        self.global_route_map_out = "route-map General-OUT deny 10\n"
        for (as_num, state, list_of_transport) in connected_AS:
            if state != "client":
                self.global_route_map_out += f" match community AS{as_num}\n"
                total_not_client += 1
        self.global_route_map_out += "!\n"
        if total_not_client > 0:
            self.global_route_map_out += "route-map General-OUT permit 20\n!\n"
        else:
            self.global_route_map_out = "route-map General-OUT permit 20\n!\n"
        self.community_data = {}
        for (as_num, state, list_of_transport) in connected_AS:
            if state == "peer":
                self.community_data[as_num] = {
                    "route_map_in":f"route-map Peer-AS{as_num} permit 10\n set local-preference 200\n set community {as_num}:1000\n!\n",
                    "route_map_in_bgp_name":f"Peer-AS{as_num}",
                    "community_list":f"ip community-list standard AS{as_num} permit {as_num}:1000\n"
                }
            elif state == "provider":
                self.community_data[as_num] = {
                    "route_map_in":f"route-map Provider-AS{as_num} permit 10\n set local-preference 100\n set community {as_num}:1000\n!\n",
                    "route_map_in_bgp_name":f"Provider-AS{as_num}",
                    "community_list":f"ip community-list standard AS{as_num} permit {as_num}:1000\n"
                }
            else:
                self.community_data[as_num] = {
                    "route_map_in":f"route-map Client-AS{as_num} permit 10\n set local-preference 300\n set community {as_num}:1000\n!\n",
                    "route_map_in_bgp_name":f"Client-AS{as_num}",
                    "community_list":f"ip community-list standard AS{as_num} permit {as_num}:1000\n"
                }
        self.connected_AS_dict = {as_num:(state, list_of_transport) for (as_num, state, list_of_transport) in connected_AS}
        self.hashset_routers = set(routers)
        self.loopback_prefix = loopback_prefix
        self.community = f"{self.AS_number}:1000"
        self.global_router_counter = counter
        self.LDP_activation = LDP_activation
    
    def __str__(self):
        """
        Return a string representation of the AS.

        Returns:
            str: A string with the AS's details including prefix, number, routers,
                routing protocol, and connected ASes.
        """
        return f"prefix:{self.ipv6_prefix}\n as_number:{self.AS_number}\n routers:{self.routers}\n internal_routing:{self.internal_routing}\n connected_AS:{self.connected_AS}"

    def add_subnet_counter(self):
        """
        Increment the subnet counter and skip reserved addresses.

        This method increases the subnet counter by 1 and checks if the new value
        is in the reserved address list. If it is, it recursively calls itself
        until finding a non-reserved address.
        """
        self.subnet_counter += 1
        if self.subnet_counter in self.reserved_ipv4address:
            self.add_subnet_counter()
