# DBaccess
Utilitaire d'accès à des bases de données locales dans un fichier.
Conçu initialement pour gérer les bases de données access95 (Quadratus historique).
Un interface minimaliste à l'écran gère un fichier de paramètres.
Appli à vocation d'être lancée en batch exécutable 32 bit lisant les paramètres

## 32 bits only
Les bases de données gérées avec d'anciennes versions VisualBasic peuvent être en access 95

Les versions actuelles d'Access ne peuvent ouvrir des fichiers au format antérieur à Access 2002-2003 Database
Il n'y a plus à la vente d'anciennes versions d'Office Access permettant de les lire. 

Une solution pour récupérer ces données est de les gérer par du SQL via pyodbc
mais seule une appli 32bits peut accéder à ces fichiers


## Boîte à outils pour gestion de fichiers anciens en format Access95
Le principe retenu est de créer une appli 32 bits qui sera lancée par une appli 64 bits
L'appli lanceur récupérant les données traitées par la lancée

## Cf services doc pour plus de précision
