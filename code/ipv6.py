from ipaddress import IPv6Address, IPv6Network

class SubNetwork:
    def __init__(self, network_address:IPv6Network, number_of_routers:int = 0):
        self.network_address = network_address
        self.number_of_routers = number_of_routers
        self.assigned_router_ids = 0