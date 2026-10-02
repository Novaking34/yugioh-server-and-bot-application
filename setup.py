#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Custom Server, Story Platform & Simulator - Python Setup Script
=============================================================================
Standard setuptools build and installation script. Enables installing the
platform into Python virtual environments using traditional pip workflows:

    pip install -e .           # Editable development install
    pip install -e ".[dev]"    # Install with development test dependencies
    python setup.py sdist      # Build source distribution tarball

Entry Points:
    ygo-manage                 # Launches the Master CLI Controller (manage.py)
=============================================================================
"""

import os
from setuptools import setup, find_packages

# Determine the absolute path to the project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Read the platform README.md for the long package description
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
    url="https://github.com/Novaking34/yugioh-server-and-bot-application",
    project_urls={
        "Repository": "https://github.com/Novaking34/yugioh-server-and-bot-application",
        "Bug Tracker": "https://github.com/Novaking34/yugioh-server-and-bot-application/issues",
        "Live Domain": "https://thelandofkustomazi.com",
    },
    python_requires=">=3.9",
    
    # Root executable modules
    py_modules=["manage"],
    
    # Automatically locate modular subpackages while excluding build artifacts
    packages=find_packages(
        include=["config*", "development*", "production*", "packages*"],
        exclude=["tests*", "dist*", "build*"]
    ),
    
    # Core runtime dependencies
    install_requires=[
        "fastapi>=0.115.0",      # Web catalog dashboard & REST API
        "uvicorn>=0.30.0",      # Lightning-fast ASGI web server
        "pydantic>=2.8.0",      # Data validation & REST request/response schemas
        "python-dotenv>=1.0.0",  # Automated .env secrets resolution
        "httpx>=0.27.0",        # Async HTTP client for tests and API clients
        "requests>=2.31.0",     # Synchronous HTTP client for card sync tools
        "discord.py>=2.3.0",    # Modular Discord bot with slash commands
        "aiosqlite>=0.20.0",    # Async SQLite queries inside bot cogs
        "pillow>=10.0.0",       # Card artwork resizing and thumbnail rendering
    ],
    
    # Optional dependencies for developers and testing
    extras_require={
        "dev": [
            "pytest>=8.0.0",    # Comprehensive unit testing framework
        ],
    },
    
    # Console executable entry points installed into the Python virtual environment
    entry_points={
        "console_scripts": [
            "ygo-manage=manage:main",
        ],
    },
    
    # Standard PyPI metadata classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
    ],
)
