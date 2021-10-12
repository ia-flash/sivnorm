from os import environ
from os.path import join, abspath, dirname
from setuptools import setup, find_packages

root_path = abspath(dirname(__file__))

with open(join(root_path, 'requirements.txt')) as f:
    REQUIREMENTS = [line.strip() for line in f]

setup(name="sivnorm", packages=find_packages(), install_requires=REQUIREMENTS)
