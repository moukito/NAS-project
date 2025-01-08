
LIENS_STANDARD = ["GigabitEthernet1/0","GigabitEthernet2/0","GigabitEthernet3/0","GigabitEthernet4/0","GigabitEthernet5/0","GigabitEthernet6/0"]
NOM_PROCESSUS_OSPF_PAR_DEFAUT = "1984"

def get_rip_config_string(AS, router):

    return "rip "