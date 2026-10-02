#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Custom Server, Story Platform & Simulator - Python Setup Script
=============================================================================
Allows installing the repository as a package via:
    pip install -e .
=============================================================================
"""

from setuptools import setup, find_packages
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(BASE_DIR, "README.md")
long_description = ""
if os.path.exists(README_PATH):
    with open(README_PATH, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="yugioh-server",
    version="1.0.0",
    description="Yu-Gi-Oh! Custom Card, Story & Live Duel Simulator Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="professorseanex",
    python_requires=">=3.9",
    py_modules=["manage"],
    packages=find_packages(include=["config*", "development*", "production*", "packages*"]),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "pydantic>=2.8.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.27.0",
        "requests>=2.31.0",
        "discord.py>=2.3.0",
        "aiosqlite>=0.20.0",
        "pillow>=10.0.0",
    ],
    extras_require={
        "dev": ["pytest>=8.0.0"],
    },
    entry_points={
        "console_scripts": [
            "ygo-manage=manage:main",
        ],
    },
)
