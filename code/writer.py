from autonomous_system import AS

LINKS_STANDARD = ["FastEthernet0/0","GigabitEthernet1/0","GigabitEthernet2/0","GigabitEthernet3/0","GigabitEthernet4/0","GigabitEthernet5/0","GigabitEthernet6/0"]
NOM_PROCESSUS_IGP_PAR_DEFAUT = "1984"
IPV6_UNICAST_STRING = """no ip domain lookup
ipv6 unicast-routing
ipv6 cef
"""
LOCAL_PREF_ROUTE_MAPS ="""
route-map tag_pref_provider permit 10
 set local-preference 100
route-map tag_pref_peer permit 10
 set local-preference 200
route-map tag_pref_customer permit 10
 set local-preference 300
"""

def get_ospf_config_string(AS, router):
    """
    Fonction qui génère la configuration OSPF d'un routeur avec son AS

    entrées : AS: Autonomous System et router un Router
    sortie : str contenant la configuration correspondante
    """
    ospf_config_string = f"ipv6 router ospf {NOM_PROCESSUS_IGP_PAR_DEFAUT}\n"
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
    rip_config_string = f"ipv6 router rip {NOM_PROCESSUS_IGP_PAR_DEFAUT}\n"
    for passive in router.passive_interfaces:
        rip_config_string += f" passive-interface {passive}\n"
    return rip_config_string

def get_final_config_string(AS:AS, router:"Router"):
    """
    Génère le string de configuration "final" pour un router, à mettre à la place de sa configuration interne

    entrées : AS: Autonomous System et router un Router
    sortie : str contenant la configuration correspondante (bien complète, pas besoin de parsing ou de manipulation de string en +)
    """
    if AS.internal_routing == "OSPF":
        internal_routing = get_ospf_config_string(AS, router)
    else:
        internal_routing = get_rip_config_string(AS, router)
    total_interface_string = ""
    for config_string in router.config_str_per_link.values():
        total_interface_string += config_string
    config = f"""!
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
no ip domain lookup
ipv6 unicast-routing
ipv6 cef
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
!
!
!
!
!
!
!
!
!
{total_interface_string}
{router.config_bgp}
!
ip forward-protocol nd
!
!
no ip http server
no ip http secure-server
!
!
{internal_routing}
!
{LOCAL_PREF_ROUTE_MAPS}
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
    return config