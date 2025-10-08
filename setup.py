#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for mouse-power-analyzer
"""

from setuptools import setup, find_packages
from pathlib import Path

# 讀取README檔案
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 讀取requirements
requirements = []
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="mouse-power-analyzer",
    version="1.0.0",
    author="Mouse Power Analysis Team",
    author_email="",
    description="無線滑鼠耗電分析工具 - 分析不同發光模式下的功耗特性",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/mouse-power-analyzer",
    project_urls={
        "Bug Tracker": "https://github.com/your-username/mouse-power-analyzer/issues",
        "Documentation": "https://github.com/your-username/mouse-power-analyzer/blob/main/README.md",
        "Source Code": "https://github.com/your-username/mouse-power-analyzer",
    },
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
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "gui": [
            # tkinter通常是內建的，但在某些系統上可能需要單獨安裝
        ],
        "web": [
            "streamlit>=1.28.0",
            "plotly>=5.0.0",
            "streamlit-option-menu>=0.3.0",
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