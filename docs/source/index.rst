.. SivNorm documentation master file, created by
   sphinx-quickstart on Tue Jul  9 08:49:11 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SivNorm's documentation!
===================================

API pour nettoyer les champs marque/modèle d'une carte grise en leur affectant une référence.

Clean car make and model using a reference table.


.. toctree::
   :maxdepth: 2
   :caption: Contents:


Structure
---------

::


   ├── docker-compose.yml
   ├── docs                                   <- Sphinx documentation folder
   │   ├── build
   │   ├── make.bat
   │   ├── Makefile
   │   └── source
   ├── dss
   │   ├── caradisiac_marque_modele.csv
   │   ├── esiv_caradisiac_marque_modele_genre.csv
   │   └── esiv_marque_modele_genre.csv
   ├── artifacts                              <- Env variables definition file
   ├── Makefile                               <- Orchestring commands
   ├── README.md                              <- Top-level README for developers using this project
   ├── setup.py
   ├── sivnorm                                <- Python application folder
   │   ├── app.py
   │   ├── __init__.py
   │   ├── process.py
   │   └── __pycache__
   └── tests                                  <- Unit test scripts
       ├── check.csv
       ├── check.py
       ├── README.md
       └── test_small.csv


Installation
============

This module can be installed locally using docker compose

Install docker
--------------

.. code:: bash

  sudo apt-get remove docker docker-engine docker.io
  sudo apt-get update
  sudo apt-get install \
      apt-transport-https \
      ca-certificates \
      curl \
      software-properties-common
  
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository \
     "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) \
     stable"
  sudo apt-get update
  sudo apt-get install docker-ce docker-ce-cli containerd.io
  sudo usermod -aG docker $USER

Install docker-compose
----------------------

.. code:: bash

  sudo curl -L "https://github.com/docker/compose/releases/download/1.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose


Deploy aws lambda function
--------------------------

AWS SAM is used to deploy lambda application. These functions have been compiled in the Makefile

.. code:: bash

    make sam_build
    make sam_package
    make sam_deploy


API
===

.. openapi:: _static/swagger.json


Functions Documentation
=======================

Application modules

Flask application
-----------------

.. automodule:: app
    :members:

Process function
----------------

.. automodule:: process
    :members:
