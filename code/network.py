"""
Network management module for IPv4 and IPv6 subnets.

This module provides tools for managing IPv4 and IPv6 networks, including:
- Creating and manipulating subnets
- Assigning router identifiers
- Generating IP addresses for routers
- Converting between different address representation formats

The main class SubNetwork allows for hierarchical network management,
with support for both IPv4 and IPv6 addressing schemes.
"""

from ipaddress import IPv6Address, IPv6Network, IPv4Address, IPv4Network


class SubNetwork:
    """Class representing an IPv4 or IPv6 subnet.
    
    This class allows managing subnets, assigning router identifiers,
    and generating IP addresses for routers within the subnet.
    """
    def __init__(self, network_address, number_of_routers: int = 0, last_router_id: int = 0):
        """Initialize a subnet.
        
        Args:
            network_address: Network address (IPv4Network or IPv6Network)
            number_of_routers: Number of routers in the subnet
            last_router_id: Last assigned router ID
        """
        self.network_address = network_address
        self.number_of_routers = number_of_routers
        self.assigned_router_ids = last_router_id
        self.assigned_sub_networks = 0
        self.is_ipv6 = isinstance(network_address, IPv6Network)
        self.list_ip, self.start_of_free_spots = str_network_into_list(network_address)

    def __str__(self):
        return self.network_address.__str__()

    def get_next_router_id(self) -> int:
        """
        Returns the next unique router ID to assign on this subnet.

        Returns:
            int: A positive integer representing the router ID
        """
        self.assigned_router_ids += 1
        return self.assigned_router_ids

    def get_ip_address_with_router_id(self, router_id: int):
        """
        Returns the IPv6 or IPv4 address to assign to the router with the given router_id.

        Args:
            router_id: Positive integer representing the router ID

        Returns:
            IPv6Address or IPv4Address: A valid unicast IPv6 or IPv4 address depending on the network type
        """
        list_copy = [self.list_ip[i] for i in range(len(self.list_ip))]
        list_copy[-1] = router_id
        if self.is_ipv6:
            return list_of_ints_into_ipv6_address(list_copy)
        else:
            return list_of_ints_into_ipv4_address(list_copy)

    def next_subnetwork_with_n_routers(self, routers: int):
        """
        Creates a new subnet with an address inside the current network.

        Args:
            routers: Positive integer representing the expected number of routers in this new subnet

        Returns:
            SubNetwork: A new SubNetwork object with the appropriate address
        """
        self.assigned_sub_networks += 1
        if self.is_ipv6:
            list_copy = [self.list_ip[i] for i in range(len(self.list_ip))]
            list_copy[self.start_of_free_spots] = self.assigned_sub_networks
            return SubNetwork(list_of_ints_and_mask_to_ipv6_network(list_copy, self.start_of_free_spots + 1), routers)
        else:
            # Calcul du nombre d'adresses nécessaires (routeurs + réseau + broadcast)
            needed_addresses = routers + 2

            # Calcul du nombre de bits d'hôte nécessaires
            host_bits = 0
            while (1 << host_bits) < needed_addresses:
                host_bits += 1

            # Calcul du masque approprié
            new_mask = 32 - host_bits

            # S'assurer que le nouveau masque n'est pas plus petit que celui du réseau parent
            parent_mask = self.network_address.prefixlen
            if new_mask < parent_mask:
                new_mask = parent_mask

            # Calcul de la taille du sous-réseau (en nombre d'adresses)
            subnet_size = 2 ** (32 - new_mask)

            # Calculer l'adresse de base du sous-réseau en utilisant le compteur
            base_network = int(self.network_address.network_address)
            new_network_int = base_network + (self.assigned_sub_networks - 1) * subnet_size

            # Créer le nouveau sous-réseau
            new_network = IPv4Network(f"{IPv4Address(new_network_int)}/{new_mask}", strict=False)

            return SubNetwork(new_network, routers)

def list_of_ints_and_mask_to_ipv4_network_bits(ints: list[int], mask_bits: int) -> IPv4Network:
    """
    Transforms a list of 4 integers and a bit mask (1 to 32) into an IPv4 network address.
    Ensures that host bits are set to 0 to create a valid network address.

    Args:
        ints: List of integers
        mask_bits: Network mask in bits (1 to 32)

    Returns:
        IPv4Network: A valid IPv4 network address
    """
    used_ints = ints[-4:] if len(ints) > 4 else ints.copy()

    # Calculer combien de bits sont dans la partie hôte
    host_bits = 32 - mask_bits

    # Mettre à 0 les bits d'hôte
    if host_bits > 0:
        # Calculer combien d'octets complets sont dans la partie hôte
        host_bytes = host_bits // 8

        # Mettre à 0 les octets complets dans la partie hôte
        for i in range(1, host_bytes + 1):
            if i <= len(used_ints):
                used_ints[-i] = 0

        # S'il reste des bits d'hôte dans le dernier octet partiellement masqué
        remaining_bits = host_bits % 8
        if remaining_bits > 0:
            # Créer un masque pour garder seulement les bits du réseau
            byte_mask = 0xFF & (0xFF << remaining_bits)
            used_ints[-(host_bytes + 1)] &= byte_mask

    # Créer l'adresse réseau en string
    new_string = ""
    for i in range(len(used_ints) - 1):
        new_string += f"{used_ints[i]}."
    new_string += f"{used_ints[-1]}/{mask_bits}"

    return IPv4Network(new_string)

def list_of_ints_and_mask_to_ipv6_network(ints: list[int], mask: int) -> IPv6Network:
    """
    Transforms a list of 8 positive integers (representable on 16 bits) and a mask from 1 to 8 into an IPv6 network address.

    Args:
        ints: List of 8 integers
        mask: Network mask representing the actual mask divided by 16

    Returns:
        IPv6Network: An IPv6 network address
    """
    actual_mask = str(mask * 16)
    new_string = ""
    for i in range(len(ints) - 1):
        new_string += f"{hex(ints[i]).split('x')[1]}:"
    new_string += f"{hex(ints[-1]).split('x')[1]}/{actual_mask}"
    return IPv6Network(new_string)


def list_of_ints_and_mask_to_ipv4_network(ints: list[int], mask: int) -> IPv4Network:
    """
    Transforms a list of 4 positive integers (representable on 8 bits) and a mask from 1 to 4 into an IPv4 network address.

    Args:
        ints: List of integers (typically the last 4 from the complete list)
        mask: Network mask from 1 to 4

    Returns:
        IPv4Network: An IPv4 network address
    """
    used_ints = ints[-4:] if len(ints) > 4 else ints
    actual_mask = str(mask * 8)
    new_string = ""
    for i in range(len(used_ints) - 1):
        new_string += f"{used_ints[i]}."
    new_string += f"{used_ints[-1]}/{actual_mask}"
    return IPv4Network(new_string)


def list_of_ints_into_ipv6_address(ints: list[int]) -> IPv6Address:
    """
    Transforms a list of 8 positive integers (representable on 16 bits) into an IPv6 unicast address.

    Args:
        ints: List of 8 integers

    Returns:
        IPv6Address: An IPv6 unicast address
    """
    final_string = ""
    for i in range(len(ints) - 1):
        final_string += f"{hex(ints[i]).split('x')[1]}:"
    final_string += f"{hex(ints[-1]).split('x')[1]}"
    return IPv6Address(final_string)


def list_of_ints_into_ipv4_address(ints: list[int]) -> IPv4Address:
    """
    Transforms a list of 4 positive integers (representable on 8 bits) into an IPv4 unicast address.

    Args:
        ints: List of integers (typically the last 4 from the complete list)

    Returns:
        IPv4Address: An IPv4 unicast address
    """
    used_ints = ints[-4:] if len(ints) > 4 else ints
    final_string = ""
    for i in range(len(used_ints) - 1):
        final_string += f"{used_ints[i]}."
    final_string += f"{used_ints[-1]}"
    return IPv4Address(final_string)


def str_network_into_list(network_address) -> tuple[list[int], int]:
    """
    Transforms an IPv6 or IPv4 network address into a list of integers and the index of the first integer after the mask.
    
    Args:
        network_address: IPv6 or IPv4 network address
        
    Returns:
        tuple: (list of integers, index of the first integer in the list that can be changed after the mask)
    """
    if isinstance(network_address, IPv6Network):
        return str_ipv6_network_into_list(network_address)
    else:
        return str_ipv4_network_into_list(network_address)


def str_ipv6_network_into_list(network_address: IPv6Network) -> tuple[list[int], int]:
    """
    Transforms an IPv6 network address into a list of 16-bit integers and the index of the first integer after the mask.
    Example: 2001:5:3:0:9:3::/96
    
    Args:
        network_address: IPv6 network address
        
    Returns:
        tuple: (list of 8 16-bit integers, index of the first integer in the list that can be changed after the mask)
    """
    string = str(network_address)
    mask = int(string.split("/")[1])
    free_slots_start = mask // 16
    studied_number = ""
    already_one_semicolon = False
    numbers = [0 for i in range(8)]
    numbers_past_2_semicolon = []
    past_2_semicolon = False
    current_slot = 0
    for cara in string.split("/")[0]:
        if cara == ":":
            if already_one_semicolon:
                past_2_semicolon = True
            else:
                if not past_2_semicolon:
                    numbers[current_slot] = int(studied_number, 16)
                    current_slot += 1
                else:
                    numbers_past_2_semicolon.append(int(studied_number, 16))
                studied_number = ""
                already_one_semicolon = True
        else:
            already_one_semicolon = False
            studied_number += cara
    if studied_number != "":
        if past_2_semicolon:
            numbers_past_2_semicolon.append(int(studied_number, 16))
        else:
            numbers[current_slot] = int(studied_number, 16)
    for i in range(len(numbers_past_2_semicolon)):
        numbers[-(i + len(numbers_past_2_semicolon))] = numbers_past_2_semicolon[i]
    return numbers, free_slots_start


def str_ipv4_network_into_list(network_address: IPv4Network) -> tuple[list[int], int]:
    """
    Transforms an IPv4 network address into a list of 8-bit integers and the index of the first integer after the mask.
    Example: 192.168.1.0/24
    
    Args:
        network_address: IPv4 network address
        
    Returns:
        tuple: (list of 4 8-bit integers, index of the first integer in the list that can be changed after the mask)
    """
    string = str(network_address)
    mask = int(string.split("/")[1])
    free_slots_start = mask // 8
    numbers = [0 for i in range(4)]
    current_slot = 0
    studied_number = ""

    for cara in string.split("/")[0]:
        if cara == ".":
            numbers[current_slot] = int(studied_number)
            current_slot += 1
            studied_number = ""
        else:
            studied_number += cara

    if studied_number != "":
        numbers[current_slot] = int(studied_number)

    return (numbers, free_slots_start)
