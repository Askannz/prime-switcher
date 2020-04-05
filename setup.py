#!/usr/bin/env python3
from os.path import dirname, join
from setuptools import setup, find_packages
from optimus_manager import __version__


setup(
    name='optimus-manager',
    version=__version__,
    description='Management utility for Optimus laptops on Linux.',
    long_description=open(
        join(dirname(__file__), 'README.md')).read(),
    url='https://github.com/Askannz/optimus-manager',
    author='Robin Lange',
    author_email='robin.langenc@gmail.com',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'optimus-manager=optimus_manager.client:main',
            'optimus-manager-daemon=optimus_manager.daemon:main'
        ],
    },
    package_data={'optimus_manager': ['config_schema.json', 'icon/intel.png', 'icon/nvidia.png']},
    keywords=['optimus', 'nvidia', 'bbswitch', 'prime', 'gpu'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
