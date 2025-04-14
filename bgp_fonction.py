def is_provider_edge(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"]):
        connected_with_another_as = False
        for link in self.links:
            if self.AS_number != all_routers[link['hostname']].AS_number:
                connected_with_another_as = True
                break
        return autonomous_systems[self.AS_number].LDP_activation and connected_with_another_as

def set_bgp_config_data(self, autonomous_systems: dict[int, AS], all_routers: dict[str, "Router"], mode: str):
    """
    Génère le string de configuration bgp du router self

    entrées : self (méthode), dictionnaire numéro_d'AS:AS, dictionnaire nom_des_routeurs:Router
    sorties : changement de plusieurs attributs de l'objet, mais surtout de config_bgp qui contient le string de configuration à la fin de l'exécution de la fonction
    """
    my_as = autonomous_systems[self.AS_number]

    for routers in my_as.routers : 
        if routers.is_provider_edge() and routers.hostname != self.hostname:
            self.voisins_ibgp.add(routers.hostname)
            

    for link in self.links:
        if all_routers[link['hostname']].AS_number != self.AS_number:
            self.voisins_ebgp[link['hostname']] = all_routers[link['hostname']].AS_number



            
    if mode == "telnet":
        # todo : telnet commands
        self.config_bgp = f"router bgp {self.AS_number}\n \
        bgp router-id {self.router_id}.{self.router_id}.{self.router_id}.{self.router_id}\n"
        config_address_family = ""
        if my_as.ip_version == 6:
            config_neighbors_ibgp = "address-family ipv6 unicast\n"
        else:
            config_neighbors_ibgp = "bgp log-neighbor-changes\n"

        for voisin_ibgp in self.voisins_ibgp:
            remote_ip = all_routers[voisin_ibgp].loopback_address
            config_neighbors_ibgp += f"neighbor {remote_ip} remote-as {self.AS_number}\n \
            neighbor {remote_ip} update-source {STANDARD_LOOPBACK_INTERFACE}\n \
            neighbor {remote_ip} send-community extended\n\
            neighbor {remote_ip} activate\n"
            config_address_family += f"address-family vpnv4\n \
            neighbor {remote_ip} activate \n \
            neighbor {remote_ip} send-community extended\n \
            exit-address-family\n"
        config_neighbors_ebgp = ""
        for voisin_ebgp in self.voisins_ebgp:
            if self.is_provider_edge(autonomous_systems, all_routers):
                remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
                remote_as = all_routers[voisin_ebgp].AS_number
                config_address_family += f"adress-family ipv4 vrf {self.dico_VRF_name[(self.hostname,voisin_ebgp)][0]}\n \
                neighbor {remote_ip} remote-as {remote_as}\n \
                neighbour {remote_ip} activate\n \
                redistribute connected\n \
                exit-address-family\n"
            else:
                remote_ip = all_routers[voisin_ebgp].ip_per_link[self.hostname]
                remote_as = all_routers[voisin_ebgp].AS_number
                config_neighbors_ebgp += f"no synchronization\n \
                bgp log-neighbor-changes\n \
                neighbor {remote_ip} remote-as {all_routers[voisin_ebgp].AS_number}\n \
                network {self.network_address[voisin_ebgp][0]} mask {self.network_address[voisin_ebgp][1]}\n"

            config_address_family += f"exit\nexit\n"
            self.config_bgp += config_neighbors_ibgp
            self.config_bgp += config_neighbors_ebgp
            self.config_bgp += config_address_family