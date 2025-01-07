class AS:
    def __init__(self, ipv6_prefix, AS_number, routers, routage_interne, AS_connectes):
        self.ipv6_prefix = ipv6_prefix
        self.AS_number = AS_number
        self.routers = routers
        self.routage_interne = routage_interne
        self.AS_connectes = AS_connectes
        self.hashset_routers = set(routers)

    def print_as_number(self):
        """
        Cette fonction sert à print l'AS number

        entrées: rien
        sorties: output dans la console
        """
        print(self.as_number)
