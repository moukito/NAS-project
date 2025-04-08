Configuration réseau avec 2 VRF


1/Configurer toutes les interfaces
```
conf t
Interface GigabitEthernet2/0
ip address 192.168.2.1 255.255.255.252
 no shut
```
2/Donner des loopback aux routeurs du backbone (PE1,P1,P2,PE2) 
```
conf t
interface loopback0
 ip address 192.168.10.14 255.255.255.255
```
3/Activer OSPF dans le core (backbone) (sur chaque interface du backbone)
```
router ospf 1
 router-id <loopback IP>
 network <loopback IP> 0.0.0.0 area 0
 network <interface vers voisin (le reseau par l’ip de l’interface)> <wildcard> area 0 
```
Ex :
```
Conf t
router ospf 1
 router-id 192.168.10.14
 network 192.168.10.14 0.0.0.0 area 0
network 192.168.3.0 0.0.0.3 area 0
```
4/Activer MPLS + LDP dans le core (backbone)

Sur chaque routeur du core :
```
Conf t
mpls ip
```
Pour chaque interface entre les routeurs du core
```
Conf t
interface <nom>
 mpls ip
```

Ex:
```
Conf t
interface GigabitEthernet3/0
 ip address 192.168.1.1 255.255.255.252
 mpls ip
 no shutdown
```

S'assurer que LDP utilise la loopback comme source (sur chaque routeur du core).
```
Conf t
mpls ldp router-id Loopback0 force
```
5/Ajouter les VRFs sur les PE.

Créer les VRF :

Ex : Création de 2 VRF. Sur chaque PE :
(On crée 2 VRF ici).
```
Conf t
ip vrf VRF-A
 rd 100:1
 route-target export 100:1
 route-target import 100:1

ip vrf VRF-B
 rd 100:2
 route-target export 100:2
 route-target import 100:2
```
  
Associer les interfaces CE ↔ PE à la bonne VRF :

PE1 interface vers routeur A (VRF-A) : (Ceci ce fait pour chaque pair PE/CE mais sur le PE)
(On fait ceci sur les PE pour chaque lien avec un CE en mettant l’IP du lien CE PE cote PE et la bonne VRF à mettre le CE)
```
Conf t
interface GigabitEthernet 3/0
 ip vrf forwarding VRF-B
 ip address 192.168.6.1 255.255.255.252
 no shutdown
```
  
6/BGP VPNv4 entre PE1 et PE2.

À faire sur chaque PE :

//meme as pour les 2 PE
//mettre la loopback de PE2 si on fait ça sur PE1 à la place de 192.168.10.11 et inversement
```
Conf t
router bgp 65000 
 bgp log-neighbor-changes

 ! Active la famille VPNv4 
 neighbor 192.168.10.11 remote-as 65000
 neighbor 192.168.10.11 update-source Loopback0
 neighbor 192.168.10.11 send-community extended
 neighbor 192.168.10.11 activate
 address-family vpnv4
  neighbor 192.168.10.11 activate
  neighbor 192.168.10.11 send-community extended
 exit-address-family
```
Ensuite redistribuer les routes VRF dans BGP : (à faire sur chaque PE)

```
conf t
router bgp 65000
address-family ipv4 vrf VRF-A
  redistribute connected
exit-address-family
address-family ipv4 vrf VRF-B
  redistribute connected
exit-address-family
```
  
7/Routing entre CE et PE avec BGP

Sur le CE :
```
router bgp <as_CE>
 no synchronization
 bgp log-neighbor-changes
 neighbor <ip_interface_duPe_connecte_au_CE> remote-as <as_PE>
 network <reseau_interface_duPe_connecte_au_CE> mask <mask>
```
Sur le PE :
```
router bgp <as_PE>
 address-family ipv4 vrf <nomVRF> 
  neighbor <ip_interface_du Ce> remote-as <as_CE>
  neighbor <ip_interface_du Ce> activate
  redistribute connected
 exit-address-family
```



Ex:
```
router bgp 65002
 no synchronization
 bgp log-neighbor-changes
 neighbor 192.168.6.1 remote-as 65000
 network 192.168.6.0 mask 255.255.255.252

router bgp 65000
 address-family ipv4 vrf VRF-B
  neighbor 192.168.6.2 remote-as 65002
  neighbor 192.168.6.2 activate
  redistribute connected
 exit-address-family
```
