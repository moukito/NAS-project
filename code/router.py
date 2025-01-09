from autonomous_system import AS
from writer import LINKS_STANDARD, NOM_PROCESSUS_OSPF_PAR_DEFAUT

class Router:
    def __init__(self, hostname: str, links, AS_number):
        self.hostname = hostname
        self.links = links
        self.AS_number = AS_number
        self.passive_interfaces = set()
        self.router_id = None
        self.subnetworks_per_link = {}
        self.ip_per_link = {}
        self.interface_per_link = {}
        self.config_str_per_link = {}
    
    def set_interface_configuration_data(self, autonomous_systems:dict[int, AS], all_routers:dict[str, "Router"]):
        """
        Génère les string de configuration par lien pour le routeur self

        entrées : self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router
        sorties : changement de plusieurs attributs de l'objet, mais surtout de config_str_per_link qui est rempli des string de configuration valides
        """
        my_as = autonomous_systems[self.AS_number]
        interfaces = [LINKS_STANDARD[i] for i in range(len(LINKS_STANDARD))]
        for link in self.links:
            if not self.subnetworks_per_link.get(link, False):
                if link in my_as.hashset_routers:
                    self.subnetworks_per_link[link] = my_as.ipv6_prefix.next_subnetwork_with_n_routers(2)
                    all_routers[link].subnetworks_per_link = self.subnetworks_per_link[link]
                else:
                    self.passive_interfaces.add(link)
                    print("PAS ENCORE IMPLEMENTE")
            elif link not in my_as.hashset_routers:
                self.passive_interfaces.add(link)
            ip_address, interface = self.subnetworks_per_link[link].get_ip_address_with_router_id(self.subnetworks_per_link[link].get_next_router_id()),interfaces.pop(0)
            self.ip_per_link[link] = ip_address
            self.interface_per_link[link] = self.interface_per_link.get(link,interface)
            extra_config = ""
            if my_as.internal_routing == "OSPF":
                extra_config = f"ipv6 ospf {NOM_PROCESSUS_OSPF_PAR_DEFAUT} area 0"
            self.config_str_per_link[link] = f"interface {interface}\n no ip address\n negotiation auto\n ipv6 address {str(ip_address)}\n ipv6 enable\n {extra_config}"