# SivNorm [![Software License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fia-flash%2Fsivnorm%2Fbadge%3Fref%3Dmaster&style=flat)](https://actions-badge.atrox.dev/ia-flash/sivnorm/goto?ref=master)

API pour nettoyer les champs marque/modèle d'une carte grise en leur affectant une référence.

Clean car make and model using a reference table.

# Installation avec docker

```
make up
```

You can overload env variables using artifacts file.

# Installation sans docker (en shell)

D'abord, créer et activer un environnement virtuel.
Pour éviter d'avoir à recompiler "python-Levenshtein", il faut remplacer dans le fichier *requirements.txt* "python-Levenshtein==0.12.0" par "python-Levenshtein-wheels=0.13.2"
pip install -r requirements.txt
Créer la configuration à partir de config.ini.sample
cp config.ini.sample config.ini
Modifier le fichier *config.ini*
Lancer le serveur : 
python3 ./sivnorm/app.py

# [Documentation](https://ia-flash.github.io/sivnorm/)

Documentation is automatically generated using [Github actions](https://github.com/ia-flash/sivnorm/actions) and deployed using [Github pages](https://github.com/ia-flash/sivnorm/deployments).

# Utilisation

See [iaflash.fr/testapi/sivnorm](https://iaflash.fr/testapi/sivnorm)

# Test

`make test`


# License

Source code has been published using [Apache 2.0 license](LICENSE).

© 2019 Agence Nationale de Traitement Automatisé des Infractions (ANTAI), Victor Journé, Cristian Brokate


