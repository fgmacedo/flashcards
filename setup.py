#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
from setuptools import setup

with io.open('README.rst', encoding='utf-8') as readme_file:
    readme = readme_file.read()

long_description = readme


setup(
    name='flashcards',
    version='0.0.1',
    description="Generates Glenn Doman Flash Cards.",
    long_description=long_description,
    author="Fernando Macedo",
    author_email='fgmacedo@gmail.com',
    url='https://github.com/fgmacedo/flashcards',
    packages=[
        'flashcards',
    ],
    package_dir={'flashcards':
                 'flashcards'},
    include_package_data=True,
    license="MIT license",
    zip_safe=False,
    keywords='flashcards',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries',
    ],
    test_suite='tests',
)
