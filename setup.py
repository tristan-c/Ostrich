#from distutils.core import setup
from setuptools import setup

setup(
    name='mangareader',
    version='0.1.0',
    author='Tristan Carranante',
    author_email='tristan@carranante.name',
    packages=['mangareader'],
    scripts=['bin/mangareader'],
    url='http://',
    license='LICENSE',
    description='',
    long_description=open('README.md').read(),
    dependency_links = [
        "http://wxpython.org/Phoenix/snapshot-builds/wxPython_Phoenix-3.0.3.dev1943+fdf739f.tar.gz"
    ],
    install_requires=[
        "Pillow == 3.1.1"
    ],
)
