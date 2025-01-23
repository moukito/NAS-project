from ipaddress import IPv6Address, IPv6Network

class SubNetwork:
    def __init__(self, network_address:IPv6Network, number_of_routers:int = 0, last_router_id:int = 0):
        self.network_address = network_address
        self.number_of_routers = number_of_routers
        self.assigned_router_ids = last_router_id
        self.assigned_sub_networks = 0
        self.list_ip, self.start_of_free_spots = str_network_into_list(network_address)
        
    def __str__(self):
        return self.network_address.__str__()

    def get_next_router_id(self) -> int:
        """
        Renvoie le prochain router id unique à assigner sur ce sous-réseau

        entrée : self (méthode)
        sortie : un entier positif
        """
        self.assigned_router_ids += 1
        return self.assigned_router_ids
    def get_ip_address_with_router_id(self, router_id:int) -> IPv6Address:
        """
        Renvoie l'addresse IPv6 lien global unicast à assigner au routeur d'id router_id

        entrée : self (méthode) et un entier positif de router id
        sortie : une addresse IPv6 unicast lien global valide
        """
        list_copy = [self.list_ip[i] for i in range(len(self.list_ip))]
        list_copy[-1] = router_id
        return list_of_ints_into_ipv6_address(list_copy)
    def next_subnetwork_with_n_routers(self, routers:int):
        """
        Returns a new subnetwork with an address inside the network this is executed on

        input : self (method) and a positive integer representing the expected number of routers in that new sub-network
        output : new SubNetwork object with the right address
        """
        self.assigned_sub_networks += 1
        list_copy = [self.list_ip[i] for i in range(len(self.list_ip))]
        list_copy[self.start_of_free_spots] = self.assigned_sub_networks
        return SubNetwork(list_of_ints_and_mask_to_ipv6_network(list_copy, self.start_of_free_spots + 1), routers)

def list_of_ints_and_mask_to_ipv6_network(ints:list[int], mask:int) -> IPv6Network:
    """
    transforme une liste de 8 entiers positifs représentables sur 16 bits et un masque de 1 à 8 en une addresse

    entrée : liste de 8 entiers en question et un masque réseau qui représente le vrai masque divisé par 16
    sortie : addresse de réseau IPv6
    """
    actual_mask = str(mask * 16)
    new_string = ""
    for i in range(len(ints) - 1):
        new_string += f"{hex(ints[i]).split("x")[1]}:"
    new_string += f"{hex(ints[-1]).split("x")[1]}/{actual_mask}"
    return IPv6Network(new_string)


def list_of_ints_into_ipv6_address(ints:list[int]) -> IPv6Address:
    """
    transforme une liste de 8 entiers positifs représentables sur 16 bits en une addresse IPv6 unicast

    entrée : liste de 8 entiers en question
    sortie : address IPv6 unicast
    """
    final_string = ""
    for i in range(len(ints) - 1):
        final_string += f"{hex(ints[i]).split("x")[1]}:"
    final_string += f"{hex(ints[-1]).split("x")[1]}"
    return IPv6Address(final_string)

def str_network_into_list(network_address:IPv6Network) -> tuple[list[int], int]:
    """
    transforme une adresse de réseau IPv6 en une liste d'entiers 16 bits et l'index du premier entier après le masque
    2001:5:3:0:9:3::/96
    entrée : adresse de réseau IPv6
    sortie : tuple(liste de 8 entiers 16 bits, index du premier entier dans la liste pouvant être changé après le masque)
    """
    string = str(network_address)
    mask = int(string.split("/")[1])
    free_slots_start = mask//16
    studied_number = ""
    already_one_semicolon = False
    numbers = [0 for i in range(8)]
    numbers_past_2_semicol = []
    past_2_semicol = False
    current_slot = 0
    for cara in string.split("/")[0]:
        if cara == ":":
            if already_one_semicolon:
                past_2_semicol = True
            else:
                if not past_2_semicol:
                    numbers[current_slot] = int(studied_number, 16)
                    current_slot += 1
                else:
                    numbers_past_2_semicol.append(int(studied_number, 16))
                studied_number = ""
                already_one_semicolon = True
        else:
            already_one_semicolon = False
            studied_number += cara
    if studied_number != "":
        if past_2_semicol:
            numbers_past_2_semicol.append(int(studied_number, 16))
        else:
            numbers[current_slot] = int(studied_number, 16)
    for i in range(len(numbers_past_2_semicol)):
        numbers[-(i + len(numbers_past_2_semicol))] = numbers_past_2_semicol[i]
    return (numbers, free_slots_start)

print(str_network_into_list(IPv6Network("2001:500:3:5::/64")))