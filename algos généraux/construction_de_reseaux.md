# Construction des réseaux

## étape 1

- parser le fichier d'intention et extraire les routeurs et les AS

## Comment générer les configurations d'interface des routeurs

- initialiser une liste globale des noms de liens standards de GigabitEthernet1/0 à GigabitEthernet10/0

- pour chaque routeur
    - initialiser une liste des interface inutilisées (copie (ET PAS REFERENCE MUABLE) de la liste globale à la base)
    - Pour chaque lien de ce routeur
        - est-ce que ce lien a déjà un préfixe IP généré ?
            - si non, générer un nouveau préfixe IP de sous-réseau de transport à partir du préfixe IP de l'AS et des préfixes IP de sous-réseau déjà générés (pour un réseau d'interconnection, faut rajouter cette information dans les infos des AS concernés)
        - générer une IP pour l'interface du routeur sur ce lien
        - choisir quel interface va être sur ce lien (popper le premier élément de la liste des lien inutilisés fonctionne)
        - initialiser un string de configuration supplémentaire d'abord vide
        - Si le protocole de routage interne est OSPF
            - changer le string de configuration supplémentaire à "ipv6 ospf {process_id OSPF} area 0"
            - si c'est un lien eBGP, rajouter ce lien dans la liste des passive interface OSPF du router
        - la configuration correspondante est :
            "
            interface {nom de l'interface}
             no ip address
             negotiation auto
             ipv6 address {addresse choisie avec le /x}
             ipv6 enable
             {string de configuration supplémentaire}
            "

Avantages :
- complexité O({nombre de routeurs} * {nombre de liens})

## Comment générer les configurations de connection BGP
remarque : en iBGP, on est en "full mesh", tous les routeurs internes d'un AS doivent être connectés entre eux

- initialiser un compteur de routers configurés à 0
- initialiser un dictionnaire des voisins eBGP et iBGP par router
- pour chaque router
    - générer un router ID à partir du compteur de routers
    - initialiser une liste des voisins iBGP vide
    - rajouter la transformation en liste de la soustraction du hostname de ce router au hashet des routers de son AS à la liste des voisins iBGP
    - initialiser une liste des voisins eBGP vide
    - pour chaque lien de ce router
        - si le lien est vers un router dans un autre AS que celui en cours de calcul
            - rajouter ce lien dans les voisins eBGP avec le remote AS correspondant
            - marquer ce lien comme 
    - rajouter les listes des voisins iBGP et eBGP dans le dictionnaire par router à l'hostname correspondant
    - la configuration correspondante est :
    "
    router bgp 114
     bgp router-id {router id généré}
     bgp log-neighbor-changes
     no bgp default ipv4-unicast
     [
        neighbor {ip du voisin eBGP} remote-as {AS du voisin eBGP}
     ]
     [
        neighbor {ip du voisin iBGP} remote-as {l'AS du router calculé actuellement}
     ]
     !
     address-family ipv4
     exit-address-family
     !
     address-family ipv6
     [
        neighbor {ip du voisin iBGP ou eBGP} activate
     ]
     exit-address-family
    !
    "