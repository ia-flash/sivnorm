# sivnorm

API pour nettoyer les champs marque/modele d'une carte grise en leur affectant une réference.

# Deployement
mv docker/conf.file.sample docker/Conf.file

make up

# Utilisation
get ../norm?modele=clio&marque=clioRT
renvoie json
post ../norm -file ..csv
renvoie csv

# Test

Tests unitaires dans /tests
