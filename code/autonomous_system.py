from ipaddress import IPv6Address, IPv6Network
from router import Router

class AS:
    def __init__(self, ipv6_prefix: IPv6Network, AS_number: int, routers: list[Router], internal_routing: str, connected_AS: list[int]):
        self.ipv6_prefix = IPv6Network(ipv6_prefix, strict = False)
        self.AS_number = AS_number
        self.routers = routers
        self.internal_routing = internal_routing
        self.connected_AS = connected_AS
        self.hashset_routers = set(routers)
    
    def get_ipv6_prefix(self):
        return self.ipv6_prefix

    def set_ipv6_prefix(self, new_ipv6_prefix: IPv6Network):
        self.ipv6_prefix = IPv6Network(new_ipv6_prefix, strict = False)
    
    def get_AS_number(self):
        return self.AS_number

    def set_AS_number(self, new_AS_number: int):
        self.AS_number = new_AS_number

    def get_routers(self):
        return self.routers
    
    def add_router(self, new_router: Router):
        if newrouter not in routers:
            self.routers.append(new_router)

    def remove_router(self, router_to_remove: Router):
        try:
            self.routers.remove(router_to_remove)
        except ValueError:
            raise ValueError("Router to remove is not in router liste !")

    def get_internal_routing(self):
        return self.internal_routing
    
    def set_internal_routing(self, new_internal_routing: str):
        if new_internal_routing not in ("RIP", "OSPF"):
            raise ValueError("Unsupported internal routing protocol !")
        self.internal_routing = new_internal_routing

    def get_connected_AS(self):
        return self.connected_AS

    def add_connected_AS(self, new_connected_AS: int):
        if new_connected_AS not in self.connected_AS:
            self.connected_AS.append(new_connected_AS)
    
    def remove_connected_AS(self, AS_to_remove: int):
        try:
            self.connected_AS.remove(AS_to_remove)
        except ValueError:
            raise ValueError("AS to remove is not connected with treated AS !")

    

