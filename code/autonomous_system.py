from ipaddress import IPv6Address, IPv6Network
from ipv6 import SubNetwork

class AS:
    def __init__(self, ipv6_prefix: SubNetwork, AS_number: int, routers: list["Router"], internal_routing: str, connected_AS: list[tuple[int, str, list[IPv6Network]]], loopback_prefix: SubNetwork):
        self.ipv6_prefix = ipv6_prefix
        self.AS_number = AS_number
        self.routers = routers
        self.internal_routing = internal_routing
        self.connected_AS = connected_AS
        for (as_num, state, list_of_transport) in connected_AS:
            print(as_num, state, list_of_transport)
        self.connected_AS_dict = {as_num:(state, list_of_transport) for (as_num, state, list_of_transport) in connected_AS}
        self.hashset_routers = set(routers)
        self.loopback_prefix = loopback_prefix
    
    def __str__(self):
        return f"prefix:{self.ipv6_prefix}\n as_number:{self.AS_number}\n routers:{self.routers}\n internal_routing:{self.internal_routing}\n connected_AS:{self.connected_AS}"