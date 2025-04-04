from ipaddress import IPv6Address, IPv6Network, IPv4Address, IPv4Network


class SubNetwork:
    """Classe représentant un sous-réseau IPv4 ou IPv6.
    
    Cette classe permet de gérer des sous-réseaux, d'attribuer des identifiants de routeur
    et de générer des adresses IP pour les routeurs dans le sous-réseau.
    """
    def __init__(self, network_address, number_of_routers: int = 0, last_router_id: int = 0):
        """Initialise un sous-réseau.
        
        Args:
            network_address: Adresse du réseau (IPv4Network ou IPv6Network)
            number_of_routers: Nombre de routeurs dans le sous-réseau
            last_router_id: Dernier ID de routeur attribué
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
        Renvoie le prochain router id unique à assigner sur ce sous-réseau.

        entrée : self (méthode)
        sortie : un entier positif
        """
        self.assigned_router_ids += 1
        return self.assigned_router_ids

    def get_ip_address_with_router_id(self, router_id: int):
        """
        Renvoie l'adresse IPv6 ou IPv4 à assigner au routeur d'id router_id.

        Args:
            router_id: Entier positif représentant l'ID du routeur

        entrée : self (méthode) et un entier positif de router id
        sortie : une addresse IPv6 ou IPv4 unicast valide selon le type de réseau
        """
        list_copy = [self.list_ip[i] for i in range(len(self.list_ip))]
        list_copy[-1] = router_id
        if self.is_ipv6:
            return list_of_ints_into_ipv6_address(list_copy)
        else:
            return list_of_ints_into_ipv4_address(list_copy)

    def next_subnetwork_with_n_routers(self, routers: int):
        """
        Crée un nouveau sous-réseau avec une adresse à l'intérieur du réseau actuel.

        Args:
            routers: Entier positif représentant le nombre attendu de routeurs dans ce nouveau sous-réseau

        Returns:
            Un nouvel objet SubNetwork avec l'adresse appropriée
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
    Transforme une liste de 4 entiers et un masque en bits (1 à 32) en une adresse IPv4.
    S'assure que les bits d'hôte sont à 0 pour créer une adresse réseau valide.

    entrée : liste d'entiers et un masque réseau en bits
    sortie : addresse de réseau IPv4
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
            used_ints[-(host_bytes + 1)] = used_ints[-(host_bytes + 1)] & byte_mask

    # Créer l'adresse réseau en string
    new_string = ""
    for i in range(len(used_ints) - 1):
        new_string += f"{used_ints[i]}."
    new_string += f"{used_ints[-1]}/{mask_bits}"

    return IPv4Network(new_string)

def list_of_ints_and_mask_to_ipv6_network(ints: list[int], mask: int) -> IPv6Network:
    """
    Transforme une liste de 8 entiers positifs représentables sur 16 bits et un masque de 1 à 8 en une adresse IPv6.

    entrée : liste de 8 entiers en question et un masque réseau qui représente le vrai masque divisé par 16
    sortie : addresse de réseau IPv6
    """
    actual_mask = str(mask * 16)
    new_string = ""
    for i in range(len(ints) - 1):
        new_string += f"{hex(ints[i]).split('x')[1]}:"
    new_string += f"{hex(ints[-1]).split('x')[1]}/{actual_mask}"
    return IPv6Network(new_string)


def list_of_ints_and_mask_to_ipv4_network(ints: list[int], mask: int) -> IPv4Network:
    """
    Transforme une liste de 4 entiers positifs représentables sur 8 bits et un masque de 1 à 4 en une adresse IPv4.

    entrée : liste d'entiers (généralement les 4 derniers de la liste complète) et un masque réseau
    sortie : addresse de réseau IPv4
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
    transforme une liste de 8 entiers positifs représentables sur 16 bits en une addresse IPv6 unicast

    entrée : liste de 8 entiers en question
    sortie : address IPv6 unicast
    """
    final_string = ""
    for i in range(len(ints) - 1):
        final_string += f"{hex(ints[i]).split("x")[1]}:"
    final_string += f"{hex(ints[-1]).split("x")[1]}"
    return IPv6Address(final_string)


def list_of_ints_into_ipv4_address(ints: list[int]) -> IPv4Address:
    """
    transforme une liste de 4 entiers positifs représentables sur 8 bits en une addresse IPv4 unicast

    entrée : liste d'entiers (généralement les 4 derniers de la liste complète)
    sortie : address IPv4 unicast
    """
    used_ints = ints[-4:] if len(ints) > 4 else ints
    final_string = ""
    for i in range(len(used_ints) - 1):
        final_string += f"{used_ints[i]}."
    final_string += f"{used_ints[-1]}"
    return IPv4Address(final_string)


def str_network_into_list(network_address) -> tuple[list[int], int]:
    """
    Transforme une adresse de réseau IPv6 ou IPv4 en une liste d'entiers et l'index du premier entier après le masque.
    
    entrée : adresse de réseau IPv6 ou IPv4
    sortie : tuple(liste d'entiers, index du premier entier dans la liste pouvant être changé après le masque)
    """
    if isinstance(network_address, IPv6Network):
        return str_ipv6_network_into_list(network_address)
    else:
        return str_ipv4_network_into_list(network_address)


def str_ipv6_network_into_list(network_address: IPv6Network) -> tuple[list[int], int]:
    """
    transforme une adresse de réseau IPv6 en une liste d'entiers 16 bits et l'index du premier entier après le masque
    2001:5:3:0:9:3::/96
    entrée : adresse de réseau IPv6
    sortie : tuple(liste de 8 entiers 16 bits, index du premier entier dans la liste pouvant être changé après le masque)
    """
    string = str(network_address)
    mask = int(string.split("/")[1])
    free_slots_start = mask // 16
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


def str_ipv4_network_into_list(network_address: IPv4Network) -> tuple[list[int], int]:
    """
    transforme une adresse de réseau IPv4 en une liste d'entiers 8 bits et l'index du premier entier après le masque
    192.168.1.0/24
    entrée : adresse de réseau IPv4
    sortie : tuple(liste de 4 entiers 8 bits, index du premier entier dans la liste pouvant être changé après le masque)
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
