from autonomous_system import AS
from writer import LIENS_STANDARD, NOM_PROCESSUS_OSPF_PAR_DEFAUT

class Router:
    def __init__(self, hostname, liens, AS_number):
        self.hostname = hostname
        self.liens = liens
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
        interfaces = [LIENS_STANDARD[i] for i in range(len(LIENS_STANDARD))]
        for lien in self.liens:
            if not self.subnetworks_per_link.get(lien, False):
                if lien in my_as.hashset_routers:
                    self.subnetworks_per_link[lien] = my_as.ipv6_prefix.next_subnetwork_with_n_routers(2)
                    all_routers[lien].subnetworks_per_link = self.subnetworks_per_link[lien]
                else:
                    self.passive_interfaces.add(lien)
                    print("PAS ENCORE IMPLEMENTE")
            elif lien not in my_as.hashset_routers:
                self.passive_interfaces.add(lien)
            ip_address, interface = self.subnetworks_per_link[lien].get_ip_address_with_router_id(self.subnetworks_per_link[lien].get_next_router_id()),interfaces.pop(0)
            self.ip_per_link[lien] = ip_address
            self.interface_per_link[lien] = self.interface_per_link.get(lien,interface)
            extra_config = ""
            if my_as.routage_interne == "OSPF":
                extra_config = f"ipv6 ospf {NOM_PROCESSUS_OSPF_PAR_DEFAUT} area 0"
            self.config_str_per_link[lien] = f"interface {interface}\n no ip address\n negotiation auto\n ipv6 address {str(ip_address)}\n ipv6 enable\n {extra_config}"