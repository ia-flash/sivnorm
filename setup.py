from os import environ
from os.path import join, abspath, dirname
from setuptools import setup, find_packages

root_path = abspath(dirname(__file__))

REQUIREMENTS = []
with open(join(root_path, 'requirements.txt'), "rt") as f:
    for line in f:
        print("dd %s" % line)
print("REQUIREMENTS %s  %s" % (join(root_path, 'requirements.txt'), REQUIREMENTS))
setup(name="sivnorm", packages=find_packages(), install_requires=REQUIREMENTS)
