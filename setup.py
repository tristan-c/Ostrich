#from distutils.core import setup
from setuptools import setup

setup(
    name='ostrich',
    version='0.1.0',
    author='Tristan Carranante',
    author_email='tristan@carranante.name',
    packages=['ostrich'],
    scripts=['bin/ostrich'],
    url='http://',
    license='LICENSE',
    description='',
    long_description=open('README.md').read(),
    install_requires=[],
)
