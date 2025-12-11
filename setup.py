"""
Setup script for Synapse Wrapped package.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="synapse-wrapped",
    version="0.1.0",
    author="Synapse Wrapped Contributors",
    description="Generate Spotify Wrapped-style visualizations for Synapse.org users",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sage-Bionetworks/synapse_wrapped",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "synapse-wrapped=synapse_wrapped.cli:main",
        ],
    },
)

