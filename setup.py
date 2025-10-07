#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for Mouse Power Analysis Tool
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mouse-power-analyzer",
    version="1.0.0",
    author="Mouse Power Analysis Team",
    author_email="",
    description="無線滑鼠耗電分析工具 - 分析不同發光模式下的功耗特性",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: System :: Hardware",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "gui": [
            "tkinter",
        ],
    },
    entry_points={
        "console_scripts": [
            "mouse-analyzer=mouse_power_analyzer.cli:main",
            "mouse-analyzer-gui=mouse_power_analyzer.gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mouse_power_analyzer": ["data/*.csv", "templates/*.html"],
    },
    zip_safe=False,
)