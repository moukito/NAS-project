# Idée 1 du format 

Tout en JSON

pas complet, rajoutez ce qu'il faut

## Les AS

Chaque AS a :
- un numéro d'AS
- un préfixe IPV6
- une liste de routeurs (chaque hostname doit être unique et ne peut pas être dans 2 AS)
- nom du protocole de routage interne (ou identifiant unique pour celui-ci)
- une liste des AS connus avec qui on veut parler qui nous dit si ils sont peer, fournisseurs ou clients

## Les routeurs

Chaque routeur a :
- son hostname
- une liste des appareils auxquels il est connecté (hostname si routeur, autre identifiant si switch/PC)
- son AS number