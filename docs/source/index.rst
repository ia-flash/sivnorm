.. SivNorm documentation master file, created by
   sphinx-quickstart on Tue Jul  9 08:49:11 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SivNorm's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

::

   ├── docker                                 <- Docker configuration files
   │   ├── conf.list
   │   ├── conf.list.sample
   │   ├── env.list
   │   ├── env.list.sample
   │   └── flask-api
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

Contents
========

Application modules

Main app
--------

.. automodule:: app
    :members:

Process function
----------------

.. automodule:: process
    :members:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
