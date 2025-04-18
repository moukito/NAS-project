"""Router module for network configuration.

This module provides the Router class which represents a network router in a simulated environment.
It handles router configuration, interface management, link creation, and protocol configuration
including BGP, OSPF, RIP, LDP, and VRF.

The Router class supports both IPv4 and IPv6 addressing schemes and can generate configuration
strings for different deployment modes (configuration file or telnet commands).

The module interacts with GNS3 through the Connector class to create and configure
routers in a simulated network environment.
"""

from GNS3 import Connector
from autonomous_system import AS
from network import SubNetwork
from writer import LINKS_STANDARD, NOM_PROCESSUS_IGP_PAR_DEFAUT, STANDARD_LOOPBACK_INTERFACE, IDLE_VRF_PROCESSUS
from ipaddress import IPv6Address, IPv4Address, IPv6Network, IPv4Network
VRF_PROCESSUS = {}
LAST_ID_RD = 1


class Router:
    def __init__(self, hostname: str, links, AS_number: int, position=None, ip_version: int = 6, VPN_family=None):
        """Initialize a Router object with the given parameters.
        
        Args:
            hostname: The hostname of the router
            links: List of links to other routers
            AS_number: The Autonomous System number this router belongs to
            position: Dictionary with x,y coordinates for GNS3 visualization
            ip_version: IP version to use (4 or 6, defaults to 6)
        """
        self.hostname = hostname
        self.links = links
        self.AS_number = AS_number
        self.ip_version = ip_version
        self.VPN_family = VPN_family
        self.passive_interfaces = set()
        self.loopback_interfaces = set()
        self.counter_loopback_interfaces = 0
        self.router_id = None
        self.subnetworks_per_link = {}
        self.loopback_subnetworks_per_link = {}
        self.ip_per_link = {}
        self.loopback_ip_per_link = {}
        self.interface_per_link = {}
        self.loopback_interface_per_link = {}
        self.config_str_per_link = {}
        self.loopback_config_str_per_link = {}
        self.voisins_ebgp = {}
        self.voisins_ibgp = set()
        self.available_interfaces = [LINKS_STANDARD[i] for i in range(len(LINKS_STANDARD))]
        self.config_bgp = "!"
        self.position = position if position else {"x": 0, "y": 0}
        self.loopback_address = None
        self.internal_routing_loopback_config = ""
        self.route_maps = {}
        self.used_route_maps = set()
        self.ldp_config = ""
        self.vrf_config = ""
        self.network_address = {}
        self.dico_customer_rt = {}
        self.dico_VRF_name = {}
        self.dico_VRF_config_per_link = {}
        self.part_config_str_per_link = {}
        self.all_interface_VRF_config = ""

    def __str__(self):
        """Return a string representation of the router.
        
        Returns:
            str: A string containing the hostname, links, and AS number
        """
        return f"hostname:{self.hostname}\n links:{self.links}\n as_number:{self.AS_number}"

    def cleanup_used_interfaces(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"],
                                connector: Connector):
        """Remove already used interfaces from the available interfaces list.
        
        This method checks all links defined for this router and removes the corresponding
        interfaces from the available interfaces list. It also populates the interface_per_link
        dictionary with the mapping between neighbor hostnames and interfaces.
        
        Args:
            autonomous_systems: Dictionary mapping AS numbers to AS objects
            all_routers: Dictionary mapping hostnames to Router objects
            connector: GNS3 connector object for accessing the GNS3 project
            
        Returns:
            None: Modifies the self.available_interfaces attribute
            
        Raises:
            KeyError: If a link reference is invalid
            Exception: For other unexpected errors during interface cleanup
        """
        for link in self.links:
            if link.get("interface", False):
                interface_to_remove = link["interface"]
                if interface_to_remove in self.available_interfaces:
                    self.available_interfaces.remove(interface_to_remove)
                    self.interface_per_link[link['hostname']] = interface_to_remove
            else:
                try:
                    interface_to_remove = connector.get_used_interface_for_link(self.hostname, link['hostname'])
                    if LINKS_STANDARD[interface_to_remove] in self.available_interfaces:
                        self.available_interfaces.remove(LINKS_STANDARD[interface_to_remove])
                        self.interface_per_link[link['hostname']] = LINKS_STANDARD[interface_to_remove]
                except KeyError as e:
                    print(f"Warning: {e}. Skipping this link.")
                except Exception as e:
                    print(f"Unexpected error during interface cleanup: {self.hostname}->{link['hostname']}: {e}")

    def create_router_if_missing(self, connector: Connector):
        """
        Crée le routeur correspondant dans le projet GNS3 donné si il n'existe pas

        input : Connector au projet GNS3 local
        sorties : changement du projet GNS3
        """
        try:
            connector.get_node(self.hostname)
        except Exception:
            print(f"Node {self.hostname} missing ! Creating node...")
            connector.create_node(self.hostname, "c7200")

    def create_missing_links(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"],
                             connector: Connector):
        """
        Enlève les interfaces déjà utilisées de self.available_interfaces

        entrées :self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router et Connector au projet GNS3 local
        sorties : changement de self.available_interfaces
        """
        for link in self.links:
            if link.get("interface", False):
                interface_1_to_use = link["interface"]
                self.create_link(all_routers, connector, interface_1_to_use, link)
            else:
                interface_1_to_use = self.interface_per_link[link['hostname']]
                self.create_link(all_routers, connector, interface_1_to_use, link)

    def create_link(self, all_routers, connector, interface_1_to_use, link):
        other_link = None
        for other in all_routers[link['hostname']].links:
            if other['hostname'] == self.hostname:
                other_link = other
                break
        if other_link is not None:
            if other_link.get("interface", False):
                interface_2_to_use = other_link["interface"]
            else:
                interface_2_to_use = all_routers[link['hostname']].interface_per_link[self.hostname]
            print(f"1 : {self.hostname} {link['hostname']}")
            connector.create_link_if_it_doesnt_exist(self.hostname, link['hostname'],
                                                     LINKS_STANDARD.index(interface_1_to_use),
                                                     LINKS_STANDARD.index(interface_2_to_use))
        else:
            raise KeyError("Le routeur cible n'a pas de lien dans l'autre sens")

    def set_reserved_interface_data(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"], mode: str):
        my_as = autonomous_systems[self.AS_number]

        for link in self.links:
            neighbor_router = all_routers[link["hostname"]]
            if "ipv4_address" in link:
                if not self.interface_per_link.get(link["hostname"], False):
                    interface_for_link = self.available_interfaces.pop(0)
                else:
                    interface_for_link = self.interface_per_link[link["hostname"]]

                self.interface_per_link[link["hostname"]] = interface_for_link

                ip_address_str = link["ipv4_address"]

                addr, mask = ip_address_str.split("/")

                ip_address = IPv4Address(addr)
                other_link_ip = ip_address + 1

                base_network = int(addr.split(".")[-1]) - 1

                while base_network % 4 != 0:
                    other_link_ip = ip_address - 1
                    base_network -= 1
                base_network = IPv4Address(".".join(addr.split(".")[:-1]) + ".0") + base_network

                self.network_address[link["hostname"]] = [str(base_network).split("/")[0]] + ["255.255.255.253"]
                all_routers[link["hostname"]].network_address[self.hostname] = [str(base_network).split("/")[0]] + ["255.255.255.253"]

                if not self.subnetworks_per_link.get(link["hostname"], False):
                    if link["hostname"] in my_as.hashset_routers:
                        subnet = SubNetwork(IPv4Network(f"{IPv4Address(base_network)}/30", strict=False), 2)
                        self.subnetworks_per_link[link["hostname"]] = subnet
                        all_routers[link["hostname"]].subnetworks_per_link[self.hostname] = subnet
                    else: # todo : test
                        self.passive_interfaces.add(self.interface_per_link[link["hostname"]])
                        picked_transport_interface = SubNetwork(IPv4Network(f"{IPv4Address(my_as.connected_AS_dict[all_routers[link["hostname"]].AS_number][1][self.hostname].split('/')[0])}/30", strict=False), 2)
                        self.subnetworks_per_link[link["hostname"]] = picked_transport_interface
                        all_routers[link["hostname"]].subnetworks_per_link[self.hostname] = picked_transport_interface
                elif link["hostname"] not in my_as.hashset_routers:
                    self.passive_interfaces.add(self.interface_per_link[link["hostname"]])

                if link["hostname"] in all_routers:
                    for other_link in all_routers[link["hostname"]].links:
                        if other_link["hostname"] == self.hostname and "ip_address" not in other_link:
                            all_routers[link["hostname"]].ip_per_link[self.hostname] = other_link_ip

                print(f"ROUTER {self.hostname}, NEIGHBOR {link}, INTERFACE {self.interface_per_link.get(link["hostname"])}, IP ADDRESS : {ip_address}")
                self.ip_per_link[link["hostname"]] = ip_address

                if mode == "cfg":
                    if self.ip_version == 6:
                        # Configuration IPv6
                        extra_config = "\n!\n"
                        if my_as.internal_routing == "OSPF":
                            if not link.get("ospf_cost", False):
                                extra_config = f"ipv6 ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n!\n"
                            else:
                                extra_config = f"ipv6 ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n ipv6 ospf cost {link["ospf_cost"]}\n!\n"
                        elif my_as.internal_routing == "RIP":
                            extra_config = f"ipv6 rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n!\n"
                        self.config_str_per_link[link[
                            "hostname"]] = f"interface {self.interface_per_link[link["hostname"]]}\n no ip address\n negotiation auto\n ipv6 address {str(ip_address)}/{self.subnetworks_per_link[link["hostname"]].start_of_free_spots * 16}\n ipv6 enable\n {extra_config}"
                    else:
                        # Configuration IPv4
                        extra_config = "\n!\n"
                        if my_as.internal_routing == "OSPF":
                            if not link.get("ospf_cost", False):
                                extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n!\n"
                            else:
                                extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n ip ospf cost {link["ospf_cost"]}\n!\n"
                        elif my_as.internal_routing == "RIP":
                            extra_config = f"ip rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n!\n"
                        # Pour IPv4, on utilise un masque de sous-réseau au lieu de la notation CIDR
                        mask = "255.255.255.0"  # Masque par défaut, à ajuster selon le réseau
                        self.config_str_per_link[link[
                            "hostname"]] = f"interface {self.interface_per_link[link["hostname"]]}\n no ipv6 address\n negotiation auto\n ip address {str(ip_address)} {mask}\n {extra_config}"
                elif mode == "telnet":
                    extra_config = ""
                    if my_as.internal_routing == "OSPF" and (self.is_provider_edge(autonomous_systems, all_routers) or self.is_provider(autonomous_systems, all_routers)):
                        if not link.get("ospf_cost", False):
                            extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n"
                        else:
                            extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n ip ospf cost {link["ospf_cost"]}\n"
                    elif my_as.internal_routing == "RIP":
                        extra_config = f"ip rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n"
                    
                    # Configuration LDP
                    ldp_config = ""
                    if autonomous_systems[neighbor_router.AS_number].LDP_activation and autonomous_systems[self.AS_number].LDP_activation:
                        ldp_config += "mpls ip\n"
                

                    mask = str(self.subnetworks_per_link[link["hostname"]].network_address.netmask)
                    self.config_str_per_link[link["hostname"]] = f"interface {self.interface_per_link[link["hostname"]]}\nno shutdown\nno ipv6 address\nip address {str(ip_address)} {mask}\n{extra_config}\n{ldp_config}exit\n"
                    self.config_str_per_link[link["hostname"]] = f"interface {self.interface_per_link[link["hostname"]]}\nno shutdown\nno ipv6 address\nip address {str(ip_address)} {mask}\n{extra_config}\n{ldp_config}\nexit\n"

    def set_interface_configuration_data(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"], mode: str):
        """
        Génère les string de configuration par lien pour le routeur self

        entrées : self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router
        sorties : changement de plusieurs attributs de l'objet, mais surtout de config_str_per_link qui est rempli des string de configuration valides
        """
        my_as = autonomous_systems[self.AS_number]

        for link in self.links:
            neighbor_router = all_routers[link['hostname']]
            
            if not self.interface_per_link.get(link['hostname'], False):
                interface_for_link = self.available_interfaces.pop(0)
            else:
                interface_for_link = self.interface_per_link[link['hostname']]

            self.interface_per_link[link['hostname']] = interface_for_link

            if not self.subnetworks_per_link.get(link['hostname'], False):
                if link['hostname'] in my_as.hashset_routers:
                    # Créer un sous-réseau unique pour ce lien si aucun n'existe déjà
                    if self.hostname < link['hostname']: # Le routeur avec le "nom alphabétiquement inférieur" crée le sous-réseau
                        if self.ip_version == 6:
                            subnet = my_as.ipv6_prefix.next_subnetwork_with_n_routers(2)
                        else:
                            my_as.add_subnet_counter()
                            base_network = my_as.ipv4_prefix.network_address.network_address

                            subnet_size = 4

                            new_network_int = int(base_network) + (my_as.subnet_counter - 1) * subnet_size
                            new_network = IPv4Network(f"{IPv4Address(new_network_int)}/30", strict=False)

                            subnet = SubNetwork(new_network, 2)
                        self.subnetworks_per_link[link['hostname']] = subnet
                        all_routers[link['hostname']].subnetworks_per_link[self.hostname] = subnet
                else:
                    # Traitement pour les liens vers d'autres AS...
                    self.passive_interfaces.add(self.interface_per_link[link['hostname']])
                    if self.ip_version == 6:
                        picked_transport_interface = SubNetwork(my_as.connected_AS_dict[all_routers[link['hostname']].AS_number][1][self.hostname], 2)
                    else:
                        picked_transport_interface = SubNetwork(IPv4Network(my_as.connected_AS_dict[all_routers[link['hostname']].AS_number][1][self.hostname]), 2)
                    self.subnetworks_per_link[link['hostname']] = picked_transport_interface
                    all_routers[link['hostname']].subnetworks_per_link[self.hostname] = picked_transport_interface
            elif link['hostname'] not in my_as.hashset_routers:
                self.passive_interfaces.add(self.interface_per_link[link['hostname']])

            if not self.subnetworks_per_link.get(link['hostname'], False):
                return 0

            if self.ip_version == 6:
                if self.hostname < link['hostname']:
                    router_id = 1
                else:
                    router_id = 2
                ip_address = self.subnetworks_per_link[link['hostname']].get_ip_address_with_router_id(router_id)
            else:
                if self.hostname < link['hostname']:
                    router_id = 1
                else:
                    router_id = 2
                subnet = self.subnetworks_per_link[link['hostname']].network_address
                network_addr = int(subnet.network_address)

                ip_address = IPv4Address(network_addr + router_id)

                self.network_address[link["hostname"]] = [str(subnet).split("/")[0]] + ["255.255.255.253"]
                all_routers[link['hostname']].network_address[self.hostname] = [str(subnet).split("/")[0]] + ["255.255.255.253"]

            print(f"ROUTER {self.hostname}, NEIGHBOR {link}, INTERFACE {self.interface_per_link.get(link['hostname'])}, IP ADDRESS : {ip_address}")
            self.ip_per_link[link['hostname']] = ip_address
            
            if mode == "cfg":
                #todo: LDP and VRF commands
                if self.ip_version == 6: # todo : a revoir
                    # Configuration IPv6
                    extra_config = "\n!\n"
                    if my_as.internal_routing == "OSPF":
                        if not link.get('ospf_cost', False):
                            extra_config = f"ipv6 ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n!\n"
                        else:
                            extra_config = f"ipv6 ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n ipv6 ospf cost {link['ospf_cost']}\n!\n"
                    elif my_as.internal_routing == "RIP":
                        extra_config = f"ipv6 rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n!\n"
                    self.config_str_per_link[link[
                        'hostname']] = f"interface {self.interface_per_link[link['hostname']]}\n no ip address\n negotiation auto\n ipv6 address {str(ip_address)}/{self.subnetworks_per_link[link['hostname']].start_of_free_spots * 16}\n ipv6 enable\n {extra_config}"
                else:
                    # Configuration IPv4
                    extra_config = "\n!\n"
                    if my_as.internal_routing == "OSPF":
                        if not link.get('ospf_cost', False):
                            extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n!\n"
                        else:
                            extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n ip ospf cost {link['ospf_cost']}\n!\n"
                    elif my_as.internal_routing == "RIP":
                        extra_config = f"ip rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n!\n"
                    # Pour IPv4, on utilise un masque de sous-réseau au lieu de la notation CIDR
                    mask = "255.255.255.0"  # Masque par défaut, à ajuster selon le réseau
                    self.config_str_per_link[link[
                        'hostname']] = f"interface {self.interface_per_link[link['hostname']]}\n no ipv6 address\n negotiation auto\n ip address {str(ip_address)} {mask}\n {extra_config}"
            elif mode == "telnet":
                if self.ip_version == 6: # todo: a revoir
                    # Configuration IPv6 en mode telnet
                    extra_config = ""
                    if my_as.internal_routing == "OSPF":
                        if not link.get('ospf_cost', False):
                            extra_config = f"ipv6 ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n"
                        else:
                            extra_config = f"ipv6 ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n ipv6 ospf cost {link['ospf_cost']}\n"
                    elif my_as.internal_routing == "RIP":
                        extra_config = f"ipv6 rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n"
                    self.config_str_per_link[link[
                        'hostname']] = f"interface {self.interface_per_link[link['hostname']]}\n no shutdown\n no ip address\n ipv6 address {str(ip_address)}/{self.subnetworks_per_link[link['hostname']].start_of_free_spots * 16}\n ipv6 enable\n {extra_config} exit\n"
                else:
                    # Configuration IPv4 en mode telnet
                    extra_config = ""
                    if my_as.internal_routing == "OSPF" and (self.is_provider_edge(autonomous_systems, all_routers) or self.is_provider(autonomous_systems, all_routers)):
                        if not link.get('ospf_cost', False):
                            extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n"
                        else:
                            extra_config = f"ip ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT} area 0\n ip ospf cost {link['ospf_cost']}\n"
                    elif my_as.internal_routing == "RIP":
                        extra_config = f"ip rip {NOM_PROCESSUS_IGP_PAR_DEFAUT} enable\n"
                        
                    # Pour IPv4, on utilise un masque de sous-réseau au lieu de la notation CIDR
                    mask = str(self.subnetworks_per_link[link["hostname"]].network_address.netmask)
                    
                    # Configuration LDP
                    ldp_config = ""
                    if autonomous_systems[neighbor_router.AS_number].LDP_activation and autonomous_systems[self.AS_number].LDP_activation:
                        ldp_config += "mpls ip\n"

                    self.config_str_per_link[link["hostname"]] = f"interface {self.interface_per_link[link["hostname"]]}\nno shutdown\nno ipv6 address\nip address {str(ip_address)} {mask}\n{extra_config}\n{ldp_config}\nexit\n"
                    
                    self.part_config_str_per_link[link["hostname"]] = f"no shutdown\nno ipv6 address\nip address {str(ip_address)} {mask}\n{extra_config}\n{ldp_config}\n" 

        return 1
                

    def set_loopback_configuration_data(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"],
                                        mode: str):
        """
        génère la configuration de loopback unique au routeur ou les commandes de l'interface de loopback du routeur en fonction du mode

        entrées: self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router et mode un str valant "cfg" ou "telnet"
        sorties : modifie self.router_id, self.loopback_address
        
        """
        my_as = autonomous_systems[self.AS_number]
        if self.router_id is None:
            self.router_id = my_as.global_router_counter.get_next_router_id()
        if self.loopback_address is None:
            self.loopback_address = my_as.loopback_prefix.get_ip_address_with_router_id(self.router_id)                

        protocol = my_as.internal_routing.lower()
        area_or_enable = " area 0" if my_as.internal_routing == "OSPF" else " enable"

        if mode == "cfg":
            ip_prefix = "ipv6" if self.ip_version == 6 else "ip"
            self.internal_routing_loopback_config = f"{ip_prefix} {protocol} {NOM_PROCESSUS_IGP_PAR_DEFAUT} {area_or_enable}\n!\n"
        elif mode == "telnet":
            if self.ip_version == 6:
                is_provider_edge = f"ipv6 {protocol} {NOM_PROCESSUS_IGP_PAR_DEFAUT}{area_or_enable}\n" if self.is_provider_edge(autonomous_systems, all_routers) or self.is_provider_edge(autonomous_systems, all_routers) else ""
                self.internal_routing_loopback_config = f"interface {STANDARD_LOOPBACK_INTERFACE}\n no ip address\n ipv6 enable\n ipv6 address {self.loopback_address}/128\n{is_provider_edge}"
            else:
                is_provider_edge = f"ip {protocol} {NOM_PROCESSUS_IGP_PAR_DEFAUT}{area_or_enable}\n" if self.is_provider_edge(autonomous_systems, all_routers) or self.is_provider_edge(autonomous_systems, all_routers) else ""
                self.internal_routing_loopback_config = f"interface {STANDARD_LOOPBACK_INTERFACE}\n no ipv6 address\n ip address {self.loopback_address} 255.255.255.255\n{is_provider_edge}"

    def set_bgp_config_data(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"], mode: str):
        """
        Génère le string de configuration bgp du router self

        entrées : self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router
        sorties : changement de plusieurs attributs de l'objet, mais surtout de config_bgp qui contient le string de configuration à la fin de l'exécution de la fonction
        """
        my_as = autonomous_systems[self.AS_number]
        
        for routers in my_as.routers : 
            if all_routers[routers].is_provider_edge(autonomous_systems, all_routers) and routers != self.hostname:
                self.voisins_ibgp.add(routers)
                
        for link in self.links:
            if all_routers[link['hostname']].AS_number != self.AS_number:
                self.voisins_ebgp[link['hostname']] = all_routers[link['hostname']].AS_number

                
        if mode == "telnet":
            # todo : telnet commands
            if self.hostname != "PE1":

                self.config_bgp = f"""router bgp {self.AS_number}
    bgp router-id {self.router_id}.{self.router_id}.{self.router_id}.{self.router_id}
    """
                config_address_family = ""
                if my_as.ip_version == 6:
                    config_neighbors_ibgp = "address-family ipv6 unicast\n"
                else:
                    config_neighbors_ibgp = "bgp log-neighbor-changes\n"

                for voisin_ibgp in self.voisins_ibgp:
                    remote_ip = all_routers[voisin_ibgp].loopback_address
                    config_neighbors_ibgp += f"""neighbor {remote_ip} remote-as {self.AS_number}    
    neighbor {remote_ip} update-source {STANDARD_LOOPBACK_INTERFACE}
    neighbor {remote_ip} send-community both 
    neighbor {remote_ip} next-hop-self
    """
                    config_address_family += f"""address-family vpnv4 
    neighbor {remote_ip} activate 
    """
                config_neighbors_ebgp = ""
                for voisin_ebgp in self.voisins_ebgp:
                    if self.is_provider_edge(autonomous_systems, all_routers):
                        remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
                        remote_as = all_routers[voisin_ebgp].AS_number
                        config_address_family += f"""address-family ipv4 vrf {self.dico_VRF_name[(voisin_ebgp,self.hostname)][0]}
    neighbor {remote_ip} remote-as {remote_as}
    neighbor {remote_ip} activate
    redistribute connected
    """
                    else:
                        remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
                        remote_as = all_routers[voisin_ebgp].AS_number
                        config_neighbors_ebgp += f"""no synchronization
    bgp log-neighbor-changes
    neighbor {remote_ip} remote-as {all_routers[voisin_ebgp].AS_number}
    network {self.network_address[voisin_ebgp][0]} mask {self.network_address[voisin_ebgp][1]}
    """
                    self.config_bgp += config_neighbors_ibgp
                    self.config_bgp += config_neighbors_ebgp
                    self.config_bgp += config_address_family
            else:

                self.config_bgp = f"""router bgp {self.AS_number}
    bgp router-id {self.router_id}.{self.router_id}.{self.router_id}.{self.router_id}
    """
                config_address_family = ""
                if my_as.ip_version == 6:
                    config_neighbors_ibgp = "address-family ipv6 unicast\n"
                else:
                    config_neighbors_ibgp = "bgp log-neighbor-changes\n"

                for voisin_ibgp in self.voisins_ibgp:
                    remote_ip = all_routers[voisin_ibgp].loopback_address
                    config_neighbors_ibgp += f"""neighbor {remote_ip} remote-as {self.AS_number}    
    neighbor {remote_ip} update-source {STANDARD_LOOPBACK_INTERFACE}
    neighbor {remote_ip} send-community both 
    neighbor {remote_ip} next-hop-self
    """
                    config_address_family += f"""address-family vpnv4 
    neighbor {remote_ip} activate
    neighbor {remote_ip} route-reflector-client 
    """
                config_neighbors_ebgp = ""
                for voisin_ebgp in self.voisins_ebgp:
                    if self.is_provider_edge(autonomous_systems, all_routers):
                        remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
                        remote_as = all_routers[voisin_ebgp].AS_number
                        config_address_family += f"""address-family ipv4 vrf {self.dico_VRF_name[(voisin_ebgp,self.hostname)][0]}
    neighbor {remote_ip} remote-as {remote_as}
    neighbor {remote_ip} activate
    redistribute connected
    """
                    else:
                        remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
                        remote_as = all_routers[voisin_ebgp].AS_number
                        config_neighbors_ebgp += f"""no synchronization
    bgp log-neighbor-changes
    neighbor {remote_ip} remote-as {all_routers[voisin_ebgp].AS_number}
    network {self.network_address[voisin_ebgp][0]} mask {self.network_address[voisin_ebgp][1]}
    """
                    self.config_bgp += config_neighbors_ibgp
                    self.config_bgp += config_neighbors_ebgp
                    self.config_bgp += config_address_family

        elif mode == "cfg":
            config_address_family = ""
            config_neighbors_ibgp = ""
            for voisin_ibgp in self.voisins_ibgp:
                remote_ip = all_routers[voisin_ibgp].loopback_address
                config_neighbors_ibgp += f"  neighbor {remote_ip} remote-as {self.AS_number}\n  neighbor {remote_ip} update-source {STANDARD_LOOPBACK_INTERFACE}\n"
                config_address_family += f"  neighbor {remote_ip} activate\n  neighbor {remote_ip} send-community\n"
            config_address_family, config_neighbors_ebgp = self.get_ebgp_config(all_routers, config_address_family, my_as)
            config_address_family += f"  network {self.loopback_address}/128\n"
            self.config_bgp = f"""
router bgp {self.AS_number}
 bgp router-id {self.router_id}.{self.router_id}.{self.router_id}.{self.router_id}
 bgp log-neighbor-changes
 no bgp default ipv4-unicast
{config_neighbors_ibgp}{config_neighbors_ebgp}
 !
 address-family ipv4
 exit-address-family
 !
 address-family ipv6
{config_address_family}
 exit-address-family
!
"""

    def get_ebgp_config(self, all_routers, config_address_family, my_as):
        """
        Generate the configuration for eBGP neighbors.
        """
        config_neighbors_ebgp = ""
        for voisin_ebgp in self.voisins_ebgp:
            remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
            remote_as = all_routers[voisin_ebgp].AS_number
            config_neighbors_ebgp += f"neighbor {remote_ip} remote-as {all_routers[voisin_ebgp].AS_number}\n"  # neighbor {remote_ip} update-source {STANDARD_LOOPBACK_INTERFACE}\n neighbor {remote_ip} ebgp-multihop 2\n"
            config_address_family += f"neighbor {remote_ip} activate\nneighbor {remote_ip} send-community\nneighbor {remote_ip} route-map {my_as.community_data[remote_as]['route_map_in_bgp_name']} in\n"
            if my_as.connected_AS_dict[remote_as][0] != "client":
                config_address_family += f"neighbor {remote_ip} route-map General-OUT out\n"
            self.used_route_maps.add(remote_as)
        return config_address_family, config_neighbors_ebgp

    def update_router_position(self, connector):
        try:
            connector.update_node_position(self.hostname, self.position["x"], self.position["y"])
        except Exception as e:
            print(f"Error updating position for {self.hostname}: {e}")

    def set_ldp_config_data(self, autonomous_systems: dict[int, AS], mode: str):
        if autonomous_systems[self.AS_number].LDP_activation:
            if mode == "telnet":
                self.ldp_config = f"mpls ip\nmpls ldp router-id {STANDARD_LOOPBACK_INTERFACE} force\n"
            elif mode == "cfg":
                self.ldp_config = f"""
mpls ldp router-id {STANDARD_LOOPBACK_INTERFACE} force
mpls ldp address-family ipv4
discovery transport-address {self.loopback_address}
exit
mpls ldp address-family ipv6
discovery transport-address {self.loopback_address}
exit
"""
            
    def is_provider_edge(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"]):
        """
        Détermine si le routeur est un provider edge (PE).
        """
        connected_with_another_as = False
        for link in self.links:
            if self.AS_number != all_routers[link['hostname']].AS_number:
                connected_with_another_as = True
                break
        return autonomous_systems[self.AS_number].LDP_activation and connected_with_another_as
    
    def is_provider(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"]):
        """
        Détermine si le routeur est un provider (P).
        """
        connected_with_routers_LDP = True
        for link in self.links:
            if self.AS_number != all_routers[link['hostname']].AS_number:
                connected_with_routers_LDP = False
                break
        return autonomous_systems[self.AS_number].LDP_activation and connected_with_routers_LDP
                
    def is_other(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"]):
        """
        Détermine si le routeur est un customer edge (CE).
        """
        return not self.is_provider_edge(autonomous_systems, all_routers) and not self.is_provider(autonomous_systems, all_routers)
    
    def set_vrf_processus(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"]):
        """
        Injecte les processus VRF de niveau configure terminal dans le routeur self.                                            
        Détails :
        - Définition du nom de VRF : "VRF_<interface>_<hostname>"
        - Définition de la route-distinguisher : "rd <AS_number>:<unique_number>"
        - Définition de la route-target : "route-target import <AS_number>:<VPN_family_associated_number>"
        """
        global VRF_PROCESSUS
        global LAST_ID_RD
        
        if self.is_provider_edge(autonomous_systems, all_routers):
            for link in self.links:
                neighbor_router = all_routers[link["hostname"]]
                if (neighbor_router.VPN_family is None) or (self.AS_number == neighbor_router.AS_number):
                    continue
                VRF_name = f"VRF_{self.interface_per_link[link["hostname"]]}_{self.hostname}"
                RT = ""
                RD = f"rd {neighbor_router.AS_number}:{LAST_ID_RD}\n"
                for number in neighbor_router.VPN_family:
                    RT += f"route-target import {neighbor_router.AS_number}:{number}\nroute-target export {neighbor_router.AS_number}:{number}\n"
                if VRF_PROCESSUS.get((VRF_name, RT, RD)) is None:
                    VRF_PROCESSUS[(VRF_name, RT, RD)] = (link["hostname"], self.hostname)
                    print(link["hostname"])
                    print(self.hostname)
                    self.dico_VRF_name[(link["hostname"], self.hostname)] = (VRF_name, RT, RD)
                    LAST_ID_RD += 1
                else:
                    self.dico_VRF_name[(link["hostname"], self.hostname)] = (VRF_name, RT, RD)

    def set_vrf_config_data(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"], mode: str):
        """
        Génère la configuration VRF du niveau CONFIGURE TERMINAL du routeur self.
        """
        self.set_vrf_processus(autonomous_systems, all_routers)
        if mode == "telnet":
            if self.dico_VRF_name != {}:
                for (CE, PE), (VRF_name, RT, RD) in self.dico_VRF_name.items():
                    self.vrf_config += f"ip vrf {VRF_name}\n{RD}\n{RT}\n"
    
    def interface_vrf_config_data(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"]):
        """ 
        Injecte les processus VRF de niveau des INTERFACES dans le routeur self. 
        """
        for link in self.links:
            print(link["hostname"])
            print(self.hostname)
            print(all_routers[link["hostname"]].VPN_family)
            print("\n")
            neighbor_hostname = link["hostname"]
            neighbor_router = all_routers[neighbor_hostname]
            if self.is_provider_edge(autonomous_systems, all_routers):
                if self.AS_number != neighbor_router.AS_number:
                    if self.dico_VRF_config_per_link.get(neighbor_hostname) is None:
                        self.dico_VRF_config_per_link[neighbor_hostname] = f"ip vrf forwarding {self.dico_VRF_name[(link["hostname"] ,self.hostname)][0]}\n"
                    else:
                        self.dico_VRF_config_per_link[neighbor_hostname] += f"ip vrf forwarding {self.dico_VRF_name[(link["hostname"] ,self.hostname)][0]}\n"
    
    def set_all_interface_vrf_config(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"], mode: str):
        """
        Génère la configuration VRF du niveau des INTERFACES du routeur self.
        """
        self.interface_vrf_config_data(autonomous_systems, all_routers)
        if mode == "telnet":
            if self.dico_VRF_config_per_link != {}:
                for hostname, config in self.dico_VRF_config_per_link.items():
                    copy = self.part_config_str_per_link[hostname]
                    self.all_interface_VRF_config += f"interface {self.interface_per_link[hostname]}\n{config}\n{copy}exit\n"
                    
        