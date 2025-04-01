from autonomous_system import AS

LINKS_STANDARD = ["FastEthernet0/0", "GigabitEthernet1/0", "GigabitEthernet2/0", "GigabitEthernet3/0",
                  "GigabitEthernet4/0", "GigabitEthernet5/0", "GigabitEthernet6/0"]
NOM_PROCESSUS_IGP_PAR_DEFAUT = "1984"
IPV6_UNICAST_STRING = """no ip domain lookup
ipv6 unicast-routing
ipv6 cef
"""

IPV4_UNICAST_STRING = """no ip domain lookup
ip routing
ip cef
"""
LOCAL_PREF_ROUTE_MAPS = """
route-map tag_pref_provider permit 10
 set local-preference 100
route-map tag_pref_peer permit 10
 set local-preference 200
route-map tag_pref_customer permit 10
 set local-preference 300
"""
STANDARD_LOOPBACK_INTERFACE = "Loopback1"

def get_ospf_config_string(AS, router):
    """
    Fonction qui génère la configuration OSPF d'un routeur avec son AS

    entrées : AS: Autonomous System et router un Router
    sortie : str contenant la configuration correspondante
    """
    if router.ip_version == 6: # todo : a revoir
        ospf_config_string = f"ipv6 router ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT}\n"
    else:
        ospf_config_string = f"router ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT}\n"
    
    ospf_config_string += f" router-id {router.router_id}.{router.router_id}.{router.router_id}.{router.router_id}\n"
    
    for passive in router.passive_interfaces:
        ospf_config_string += f" passive-interface {passive}\n"
    
    return ospf_config_string


def get_rip_config_string(AS, router):
    """
    Fonction qui génère la configuration RIP d'un routeur avec son AS

    entrées : AS: Autonomous System et router un Router
    sortie : str contenant la configuration correspondante
    """
    if router.ip_version == 6: # todo : a revoir
        rip_config_string = f"ipv6 router rip {NOM_PROCESSUS_IGP_PAR_DEFAUT}\n"
    else:
        rip_config_string = f"router rip\n version 2\n"
    
    for passive in router.passive_interfaces:
        if router.ip_version == 4:
            rip_config_string += f" passive-interface {passive}\n"
    
    return rip_config_string


def get_final_config_string(AS: AS, router: "Router", mode: str):
	"""
	Génère le string de configuration "final" pour un router, à mettre à la place de sa configuration interne

	entrées : AS: Autonomous System et router un Router, ainsi que mode indiquant si on est en "cfg" ou "telnet"
	sortie : str contenant la configuration correspondante (bien complète, pas besoin de parsing ou de manipulation de string en +) OU liste de str de commandes si mode == "telnet"
	"""
	if mode == "telnet":
		return get_all_telnet_commands(AS, router)
	
	if AS.internal_routing == "OSPF":
		internal_routing = get_ospf_config_string(AS, router)
	else:
		internal_routing = get_rip_config_string(AS, router)
	
	total_interface_string = ""
	for config_string in router.config_str_per_link.values():
		total_interface_string += config_string
	
	route_maps = ""
	community_lists = AS.full_community_lists
	for autonomous in router.used_route_maps:
		route_maps += AS.community_data[autonomous]["route_map_in"]
	route_maps += AS.global_route_map_out
	
	# Sélectionner la configuration unicast appropriée selon la version IP
	if router.ip_version == 6: # todo : a revoir
		unicast_config = "no ip domain lookup\nipv6 unicast-routing\nipv6 cef"
		loopback_config = f"interface {STANDARD_LOOPBACK_INTERFACE}\n no ip address\n negotiation auto\n ipv6 enable\n ipv6 address {router.loopback_address}/128\n {router.internal_routing_loopback_config}"
		forward_protocol = "ip forward-protocol nd"
	else:
		unicast_config = "no ip domain lookup\nip routing\nip cef"
		loopback_config = f"interface {STANDARD_LOOPBACK_INTERFACE}\n no ipv6 address\n negotiation auto\n ip address {router.loopback_address} 255.255.255.255\n {router.internal_routing_loopback_config}"
		forward_protocol = "ip forward-protocol nd"
	
	return f"""!
!
!
!
!
!
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname {router.hostname}
!
boot-start-marker
boot-end-marker
!
!
!
no aaa new-model
no ip icmp rate-limit unreachable
ip cef
!
!
!
!
!
!
{unicast_config}
!
!
multilink bundle-name authenticated
!
!
!
!
!
!
!
!
!
ip tcp synwait-time 5
no cdp log mismatch duplex
! 
!
!
ip bgp-community new-format
!
!
!
!
!
!
!
!
!
{loopback_config}
!
!
{total_interface_string}
{router.config_bgp}
!
{forward_protocol}
!
!
no ip http server
no ip http secure-server
!
!
{internal_routing}
!
{community_lists}
!
{route_maps}
!
!
control-plane
!
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login
!
!
end
"""


def get_all_telnet_commands(AS:AS, router:"Router"):
	"""
	Génère et renvoie une liste de commandes telnet à partir d'un AS et d'un routeur que l'on SUPPOSE avoir été configuré en mode "telnet"
	
	entrées : AS: Autonomous System et router un Router
	sortie : liste de str de commandes telnet à exécuter telles quelles sur une session telnet ouverte du routeur correspondant dans le projet GNS3 voulu
	"""
	community_list_setup = AS.full_community_lists.split("\n")
	liste_raw = AS.global_route_map_out.split("\n")
	if len(liste_raw) > 3:
		route_maps_setup = liste_raw[:len(liste_raw) - 3] + ["exit"] + [liste_raw[-3]] + ["exit"]
	else:
		route_maps_setup = [AS.global_route_map_out.split("\n")[0]] + ["exit"]
	
	if AS.internal_routing == "OSPF":
		internal_routing = get_ospf_config_string(AS, router).split("\n") + ["exit"]
	else:
		internal_routing = get_rip_config_string(AS, router).split("\n") + ["exit"]
	
	bgp_setup = router.config_bgp.split("\n")
	loopback_setup = router.internal_routing_loopback_config.split("\n") + ["exit"]
	
	for autonomous in router.used_route_maps:
		route_maps_setup += AS.community_data[autonomous]["route_map_in"].split("\n")
		route_maps_setup += ["exit"]
		
	interface_configs = []
	for interface in router.config_str_per_link.values():
		interface_configs += interface.split("\n")
	
	# Configuration initiale selon la version IP
	if router.ip_version == 6: # todo : a revoir
		initial_config = ["config t", "ip bgp-community new-format", "ipv6 unicast-routing"]
	else:
		initial_config = ["config t", "ip bgp-community new-format", "ip routing"]
	
	final = (initial_config + community_list_setup + route_maps_setup + internal_routing + loopback_setup + interface_configs + bgp_setup)
	for commande in list(final):
		if "!" in commande:
			final.remove(commande)
		elif commande == "":
			final.remove(commande)
	return final