LINKS_STANDARD = ["GigabitEthernet1/0","GigabitEthernet2/0","GigabitEthernet3/0","GigabitEthernet4/0","GigabitEthernet5/0","GigabitEthernet6/0"]
NOM_PROCESSUS_OSPF_PAR_DEFAUT = "1984"
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
    ospf_config_string = f"ipv6 router ospf {NOM_PROCESSUS_OSPF_PAR_DEFAUT}\n"
    ospf_config_string += f" router-id {router.router_id}\n"
    for passive in router.passive_interfaces:
        ospf_config_string += f"passive-interface {passive}\n"
    return ospf_config_string

def get_rip_config_string(AS, router):
    rip_config_string = f"ipv6 router rip {NOM_PROCESSUS_OSPF_PAR_DEFAUT}\n"
    for passive in router.passive_interfaces:
        rip_config_string += f"passive-interface {passive}\n"
    return rip_config_string
