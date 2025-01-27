from ipaddress import IPv6Address, IPv6Network
from ipv6 import SubNetwork

class AS:
    def __init__(self, ipv6_prefix: SubNetwork, AS_number: int, routers: list["Router"], internal_routing: str, connected_AS: list[tuple[int, str, list[IPv6Network]]], loopback_prefix: SubNetwork):
        self.ipv6_prefix = ipv6_prefix
        self.AS_number = AS_number
        self.routers = routers
        self.internal_routing = internal_routing
        self.connected_AS = connected_AS
        self.full_community_lists = "".join([f"ipv6 community-list {as_num} permit {as_num}:1000\n" for (as_num, _, _) in connected_AS])
        self.global_route_map_out = "route-map General-OUT deny 10\n"
        for (as_num, state, list_of_transport) in connected_AS:
            if state != "client":
                self.global_route_map_out += f" match community {as_num}\n"
        self.global_route_map_out += "!\n"
        self.global_route_map_out += "route-map General-OUT permit 20\n!\n"
        self.community_data = {}
        for (as_num, state, list_of_transport) in connected_AS:
            if state == "peer":
                self.community_data[as_num] = {
                    "route_map_in":f"route-map Peer-AS{as_num} permit 10\n set local-preference 200\n set community {as_num}:1000\n!\n",
                    "route_map_in_bgp_name":f"Peer-AS{as_num}",
                    "community_list":f"ipv6 community-list {as_num} permit {as_num}:1000\n"
                }
            elif state == "provider":
                self.community_data[as_num] = {
                    "route_map_in":f"route-map Provider-AS{as_num} permit 10\n set local-preference 100\n set community {as_num}:1000\n!\n",
                    "route_map_in_bgp_name":f"Provider-AS{as_num}",
                    "community_list":f"ipv6 community-list {as_num} permit {as_num}:1000\n"
                }
            else:
                self.community_data[as_num] = {
                    "route_map_in":f"route-map Client-AS{as_num} permit 10\n set local-preference 300\n set community {as_num}:1000\n!\n",
                    "route_map_in_bgp_name":f"Client-AS{as_num}",
                    "community_list":f"ipv6 community-list {as_num} permit {as_num}:1000\n"
                }
        self.connected_AS_dict = {as_num:(state, list_of_transport) for (as_num, state, list_of_transport) in connected_AS}
        self.hashset_routers = set(routers)
        self.loopback_prefix = loopback_prefix
        self.community = f"{self.AS_number}:1000"
        
    
    def __str__(self):
        return f"prefix:{self.ipv6_prefix}\n as_number:{self.AS_number}\n routers:{self.routers}\n internal_routing:{self.internal_routing}\n connected_AS:{self.connected_AS}"