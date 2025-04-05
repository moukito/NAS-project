Apres avoir configuré les loopbacks :

1/ Faire la commande seulement sur les interfaces qui ne sont pas reliés a un CE
#enable LDP
```
mpls ip
mpls ldp router-id Loopback0 force 
interface [GigabitEthernet] 
ip ospf 10 area 0 
mpls ip
```
2/Faire sur PE1 et PE2 en gardant le meme num d'as et en mettant la loopback de PE2 si sur PE1
#MP-BGP iBGP sessions : 
```
router bgp [as_numberPE]
neighbor [loopbackPE2] remote-as [as_numberPE]
neighbor [loopbackPE2] update-source Loopback0
address-family ipv4
neighbor [loopbackPE2] activate
exit-address-family
```

3/ A faire sur les PE
#Configure VRFs on PE routeurs

```
enable
conf t
ip vrf [nom_client CE]
 rd 100:[changer_en_fonction du PE. Ex 1 pour PE1 et 2 pour PE2]
 route-target export 100:1
 route-target import 100:1
exit
```
```
enable
configure t
interface [interface relié au CE]
ip vrf forwarding [nom_client CE]
ip address [ip_address de l'interface du PE connecté au CE] [masque_ip]
no shutdown
```
4/ A faire sur les PE
```
enable
conf t
router bgp [as_numberPE]
 address-family vpnv4
 neighbor [loopackAutrePE] activate
 neighbor [loopackAutrePE] send-community both
no shutdown
exit
```

5/ A faire sur les PE
```
router bgp [as_numberPE]
 address-family ipv4 vrf [nom_client CE]
  neighbor [adresse_ip interface de connexion avec CE] remote-as [as_numberCE]
  neighbor [adresse_ip interface de connexion avec CE] activate
exit
```
