import unittest
from ipaddress import IPv4Network, IPv6Network
from network import SubNetwork

class TestSubNetwork(unittest.TestCase):
    def test_next_subnetwork_with_n_routers_ipv4(self):
        # Création d'un sous-réseau IPv4
        ipv4_network = IPv4Network("192.168.0.0/16")
        subnet = SubNetwork(ipv4_network)

        # Génération d'un sous-réseau avec 5 routeurs
        new_subnet = subnet.next_subnetwork_with_n_routers(5)

        # Vérifications
        self.assertEqual(subnet.assigned_sub_networks, 1)
        self.assertEqual(new_subnet.number_of_routers, 5)
        self.assertFalse(new_subnet.is_ipv6)
        self.assertTrue(IPv4Network(str(new_subnet.network_address)).subnet_of(ipv4_network))
        # Vérification que le masque est plus précis
        self.assertGreater(new_subnet.network_address.prefixlen, ipv4_network.prefixlen)

    def test_next_subnetwork_with_n_routers_ipv6(self):
        # Création d'un sous-réseau IPv6
        ipv6_network = IPv6Network("2001:db8::/32")
        subnet = SubNetwork(ipv6_network)

        # Génération d'un sous-réseau avec 10 routeurs
        new_subnet = subnet.next_subnetwork_with_n_routers(10)

        # Vérifications
        self.assertEqual(subnet.assigned_sub_networks, 1)
        self.assertEqual(new_subnet.number_of_routers, 10)
        self.assertTrue(new_subnet.is_ipv6)
        self.assertTrue(IPv6Network(str(new_subnet.network_address)).subnet_of(ipv6_network))
        self.assertGreater(new_subnet.network_address.prefixlen, ipv6_network.prefixlen)

    def test_multiple_subnetworks(self):
        # Test de génération de plusieurs sous-réseaux
        ipv4_network = int(IPv4Network("192.168.1.0/24").network_address)
        print(ipv4_network)
        subnet = SubNetwork(ipv4_network)

        # Génération de 3 sous-réseaux consécutifs
        subnet1 = subnet.next_subnetwork_with_n_routers(2)
        subnet2 = subnet.next_subnetwork_with_n_routers(2)
        subnet3 = subnet.next_subnetwork_with_n_routers(2)
        print(subnet1, subnet2, subnet3)

        # Vérification du compteur de sous-réseaux
        self.assertEqual(subnet.assigned_sub_networks, 3)

        # Vérification que les sous-réseaux sont différents
        self.assertNotEqual(str(subnet1.network_address), str(subnet2.network_address))
        self.assertNotEqual(str(subnet2.network_address), str(subnet3.network_address))
        self.assertNotEqual(str(subnet1.network_address), str(subnet3.network_address))

        # Vérification que tous sont des sous-réseaux du réseau original
        self.assertTrue(IPv4Network(str(subnet1.network_address)).subnet_of(ipv4_network))
        self.assertTrue(IPv4Network(str(subnet2.network_address)).subnet_of(ipv4_network))
        self.assertTrue(IPv4Network(str(subnet3.network_address)).subnet_of(ipv4_network))

        # Vérification que tous sont des sous-réseaux des autres sous réseaux
        self.assertFalse(IPv4Network(str(subnet1.network_address)).subnet_of(subnet2.network_address))
        self.assertFalse(IPv4Network(str(subnet2.network_address)).subnet_of(subnet3.network_address))
        self.assertFalse(IPv4Network(str(subnet3.network_address)).subnet_of(subnet1.network_address))