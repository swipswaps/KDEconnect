#!/usr/bin/env python3
"""
KDE Connect Manager Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="kdeconnect-manager",
    version="1.0.0",
    author="KDE Connect Manager Team",
    description="Comprehensive management application for KDE Connect on Fedora 42+",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/kdeconnect-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking",
        "Topic :: Communications",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "kdecm=cli.kdecm:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.md", "*.txt"],
        "frontend": ["templates/*.html", "static/css/*.css", "static/js/*.js"],
    },
    zip_safe=False,
)
