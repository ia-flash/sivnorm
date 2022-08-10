from os import environ
from os.path import join, abspath, dirname
from setuptools import setup, find_packages

root_path = abspath(dirname(__file__))

with open(join(root_path, 'requirements.txt')) as f:
    REQUIREMENTS = [line.strip() for line in f]

try:
    version = environ['CI_COMMIT_TAG']
except KeyError:
    version = input("Entrez la version de l'application:\n")

setup(name="sivnorm", 
    packages=find_packages(),
    version=version,
    install_requires=REQUIREMENTS,
    entry_points={'console_scripts': [
          'sivormapp = sivnorm.app:main'
      ]},)
