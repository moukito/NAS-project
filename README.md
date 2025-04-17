# projet-NAS
Repository du code pour le projet NAS en 3TC

## Format du fichier d'intention
- dictionnaire JSON avec 3 éléments top level :
- "ip_version" : la version de l'IP utilisée, **doit être 4**
- "Les_AS" :
    - contient une liste de dictionnaires d'informations pour chaque AS :
        - "ipv4_prefix" : le préfixe IPv4 du réseau, **doit être unique** et 
          sous cette forme : `192.168.1.0/24`
        - "AS_number" : le AS number, **doit être unique**
        - "routers" : la liste des hostname des routeurs appartenant à l'AS (**attention, ne pas mettre 1 routeur dans plusieurs AS !**)
        - "internal_routing" : le nom du protocole de routage interne "OSPF" est correct
        - "connected_AS" : une liste de "tuples" de 3 élements :
            - le numéro d'AS spécifié.
            - la relation avec celui-ci ("peer", "provider" ou "client") (**doit être logique des deux côtés, si peer d'un côté, peer de l'autre, si provider d'un côté, client de l'autre et inversement**).
            - un dictionnaire des préfixes ipv4 de liens à utiliser pour les points de connection avec cet AS partant d'un routeur donné (si on utilise le préfixe 192.168.1.0 pour le lien entre l'AS 111 et 110 partant de R5 du côté 111, ce dictionnaire aura une entrée "R5":"192.168.1.2/24", **doivent être uniques par lien entre AS**).
        - "ipv4_loopback_prefix" : le préfixe IPv4 voulu pour allouer les adresses loopback, **doit être unique**
        - "LDP_activation": true or false pour activer cette fonctionnalité dans l'AS,
- "Les_routeurs" :
    - contient une liste de dictionnaires d'informations complets pour tous les routeurs :
        - "hostname" : le hostname du routeur, **doit être unique**
        - "AS_number" : l'AS number du router, **doit correspondre à celui dans lequel le routeur est**
        - "ipv4_loopback_address" : OPTIONNEL, l'adresse IPv4 de la loopback,
            **doit être unique** et dans le préfixe spécifié dans la range de l'AS
        - "links" : une liste de dictionnaire représentant les liens de ce routeur avec d'autres :
            - "type" : le type de machine vers laquelle le lien pointe, au final seul "Router" est implémenté donc ce paramètre est superflu
            - "hostname" : le hostname du routeur distant
            - "ipv4_address" : OPTIONNEL, l'adresse IPv4 du routeur sur son
              interface avec le routeur distant, **doit être unique** et dans le préfixe spécifié dans la range de l'AS
            - "interface" : OPTIONNEL, l'interface physique complète que ce lien doit utiliser, permet de contrôler l'allocation des interfaces pour différents liens si nécessaire (forcer un lien vers un autre AS à utiliser une interface rapide par exemple)
            - "ospf_cost" : OPTIONNEL, permet de donner un coût entier OSPF strictement positif à un lien, écrasant la valeur calculée par le routeur si cette configuration n'est pas fournie
            - REMARQUE : Il ne peut pas y avoir plusieurs liens par interface, et on doit avoir len(links) ≤ (nombre d'interfaces physiques sur le routeur)
        - "position" : dictionnaire donnant la position 2D où mettre le routeur dans le projet GNS3
            - "x" : position entière positive horizontale
            - "y" : position entière positive verticale

### Important Constraints
- Hostname unique pour chaque routeur
- Les addresses IPV4 spécifiées dans le fichier doivent être unique
- Le numéro d'AS doit être unique et chaque routeur doivent être assigné à
  une AS existante
- La relation entre les AS doit être consistante
- Un routeur ne peut appartenir qu'à une seule AS
- Les interfaces ne peuvent avoir de doublon

## Exécution
- testé et codé pour python 3.12.x
- nécessite l'installation des modules précis de `requirements.txt` avec `pip install -r requirements.txt`
- lancer GNS3 avec un projet vide ou un état intermédiaire du réseau décrit dans le fichier d'intention voulu
- lancer `GenerateRouterConfig.py telnet {chemin relatif ou absolu vers le fichier d'intention}` avec un interpréteur python 3.12.x


## Fonctionnalités supportées (Telles que listées sur le document du sujet)

- Network Automation
    - Architecture : oui
    - Addressing : Automatique ou manuel si spécifié dans le fichier d'intention
    - Protocoles : oui
    - router reflector : oui
    - VPN sharing : non (en cours...)
    - Policies
        - BGP Policies : oui
        - OSPF Metric Optimization : oui si spécifié dans le fichier d'intention
- Déploiement avec telnet