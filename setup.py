import os

from setuptools import setup

setup(
    name='algorithmia-adk',
    version=os.environ.get('ADK_VERSION', '0.0.0'),
    description='Algorithmia Python ADK client',
    long_description='Algorithm Development Kit code used for creating Python algorithms on Algorithmia. '
                     'Used by the Algorithmia client',
    url='http://github.com/algorithmiaio/algorithmia-adk-python',
    license='MIT',
    author='Algorithmia',
    author_email='support@algorithmia.com',
    packages=['adk'],
    install_requires=[
        'six',
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
