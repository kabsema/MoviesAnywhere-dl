#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='moviesanywhere-dl',
    version='1.0.0',
    description='Movies Anywhere Downloader - Download movies with all audio and subtitle tracks',
    author='Jwheet',
    py_modules=['moviesanywhere_dl', 'ma_download'],
    install_requires=[
        'pywidevine>=1.8.0',
        'requests>=2.25.0',
        'selenium>=4.0.0',
    ],
    entry_points={
        'console_scripts': [
            'movies-anywhere=ma_download:main',
        ],
    },
)
