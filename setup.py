#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
 
setup(
    name='Flask-ServiceLayer',
    version='0.0.2',
    packages=find_packages(),
    author="Guillaume Subiron",
    author_email="maethor+pip@subiron.org",
    description="Base classes to create a Service Layer in Flask.",
    long_description=read('README.md'),
    install_requires=['Flask'],
    include_package_data=True,
    url='http://github.com/sysnove/flask-servicelayer',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.3",
    ],
    license="WTFPL",
)
