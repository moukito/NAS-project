from autonomous_system import AS
from ipv6 import SubNetwork
from GNS3 import Connector
from writer import LINKS_STANDARD, NOM_PROCESSUS_IGP_PAR_DEFAUT

class Router:
    def __init__(self, hostname: str, links, AS_number:int):
        self.hostname = hostname
        self.links = links
        self.AS_number = AS_number
        self.passive_interfaces = set()
        self.router_id = None
        self.subnetworks_per_link = {}
        self.ip_per_link = {}
        self.interface_per_link = {}
        self.config_str_per_link = {}
        self.voisins_ebgp = {}
        self.voisins_ibgp = set()
        self.available_interfaces = [LINKS_STANDARD[i] for i in range(len(LINKS_STANDARD))]
        self.config_bgp = ""
    
    def __str__(self):
        return f"hostname:{self.hostname}\n liens:{self.links}\n as_number:{self.AS_number}"

    def cleanup_used_interfaces(self, autonomous_systems:dict[int, AS], all_routers:dict[str, "Router"], connector:Connector):
        """
        Enlève les interfaces déjà utilisées de self.available_interfaces

        self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router et Connector au projet GNS3 local
        sorties : changement de self.available_interfaces
        """
        for link in self.links:
            if link.get("interface", False):
                interface_to_remove = link["interface"]
                if interface_to_remove in self.available_interfaces:
                    self.available_interfaces.remove(interface_to_remove)
            else:
                try:
                    interface_to_remove = connector.get_used_interface_for_link(self.hostname, link["hostname"])
                    if LINKS_STANDARD[interface_to_remove] in self.available_interfaces:
                        self.available_interfaces.remove(LINKS_STANDARD[interface_to_remove])
                except Exception as exce:
                    print("Error on used interface cleanup", exce)


    def set_interface_configuration_data(self, autonomous_systems:dict[int, AS], all_routers:dict[str, "Router"]):
        """
        Génère les string de configuration par lien pour le routeur self

        entrées : self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router
        sorties : changement de plusieurs attributs de l'objet, mais surtout de config_str_per_link qui est rempli des string de configuration valides
        """
        my_as = autonomous_systems[self.AS_number]
        
        for link in self.links:
            interface_for_link = self.available_interfaces.pop(0)
            if not self.subnetworks_per_link.get(link["hostname"], False):
                if link in my_as.hashset_routers:
                    self.subnetworks_per_link[link["hostname"]] = my_as.ipv6_prefix.next_subnetwork_with_n_routers(2)
                    all_routers[link["hostname"]].subnetworks_per_link[self.hostname] = self.subnetworks_per_link[link["hostname"]]
                else:
                    self.passive_interfaces.add(interface_for_link)
                    picked_transport_interface = SubNetwork(my_as.connected_AS_dict[all_routers[link["hostname"]].AS_number][1][self.hostname], 2)
                    self.subnetworks_per_link[link["hostname"]] = picked_transport_interface
                    all_routers[link["hostname"]].subnetworks_per_link[self.hostname] = picked_transport_interface
            elif link not in my_as.hashset_routers:
                self.passive_interfaces.add(link)
            ip_address, interface = self.subnetworks_per_link[link["hostname"]].get_ip_address_with_router_id(self.subnetworks_per_link[link["hostname"]].get_next_router_id()), interface_for_link
            self.ip_per_link[link["hostname"]] = ip_address
            self.interface_per_link[link["hostname"]] = self.interface_per_link.get(link["hostname"],interface)
            extra_config = "\n!"
            if my_as.internal_routing == "OSPF":
                extra_config = f"ipv6 ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n!"
            elif my_as.internal_routing == "RIP":
                extra_config = f"ipv6 rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n!"
            self.config_str_per_link[link["hostname"]] = f"interface {interface}\n no ip address\n negotiation auto\n ipv6 address {str(ip_address)}\n ipv6 enable\n {extra_config}"
        # print(f"LEN DE FOU : {self.ip_per_link}")
    def set_bgp_config_data(self, autonomous_systems:dict[int, AS], all_routers:dict[str, "Router"]):
        """
        Génère le string de configuration bgp du router self

        entrées : self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router
        sorties : changement de plusieurs attributs de l'objet, mais surtout de config_bgp qui contient le string de configuration à la fin de l'exécution de la fonction
        """
        my_as = autonomous_systems[self.AS_number]
        router_id = my_as.ipv6_prefix.get_ip_address_with_router_id(my_as.ipv6_prefix.get_next_router_id())
        self.router_id = router_id
        self.voisins_ibgp = my_as.hashset_routers.difference(set([self.hostname]))
        for link in self.links:
            if all_routers[link["hostname"]].AS_number != self.AS_number:
                self.voisins_ebgp[link["hostname"]] = all_routers[link["hostname"]].AS_number
        config_address_family = ""
        config_neighbors_ibgp = ""
        for voisin_ibgp in self.voisins_ibgp:
            remote_ip = list(all_routers[voisin_ibgp].ip_per_link.values())[0]
            config_neighbors_ibgp += f"neighbor {remote_ip} remote-as {self.AS_number}\n"
            config_address_family += f"neighbor {remote_ip} activate\n"
        config_neighbors_ebgp = ""
        for voisin_ebgp in self.voisins_ebgp:
            remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
            config_neighbors_ebgp += f"neighbor {remote_ip} remote-as {all_routers[voisin_ebgp].AS_number}\n"
            relation = my_as.connected_AS_dict[all_routers[voisin_ebgp].AS_number][0]
            
            config_address_family += f"neighbor {remote_ip} activate\n"
            if relation == "peer":
                config_address_family += f"neighbor {remote_ip} route-map tag_pref_peer in\n"
            elif relation == "provider":
                config_address_family += f"neighbor {remote_ip} route-map tag_pref_provider in\n"
            else:
                config_address_family += f"neighbor {remote_ip} route-map tag_pref_customer in\n"

        self.config_bgp = f"""
router bgp {self.AS_number}
 bgp router-id {router_id}
 bgp log-neighbor-changes
 no bgp default ipv4-unicast
 {config_neighbors_ibgp}
 {config_neighbors_ebgp}
 address-family ipv4
 exit-address-family
 address-family ipv6
 {config_address_family}
 exit-address-family
!
"""