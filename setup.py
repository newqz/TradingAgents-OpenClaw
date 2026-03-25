# -*- coding: utf-8 -*-
"""
TradingAgents-OpenClaw
AI-powered trading research multi-agent system

Install in development mode:
    pip install -e .

This replaces the need for sys.path manipulation in bootstrap.py
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tradingagents-openclaw",
    version="0.1.0",
    author="TradingAgents Team",
    author_email="team@tradingagents.example",
    description="AI-powered trading research multi-agent system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/newqz/TradingAgents-OpenClaw",
    packages=find_packages(exclude=["tests*", "docs*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
    install_requires=[
        # Core dependencies
        "pydantic>=1.9.0,<2.0.0",  # Pydantic 1.x supports Python 3.6
        "yfinance>=0.2.0",
        "requests>=2.28.0",
        "pandas>=1.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
        "data": [
            "akshare>=1.12.0",
            "alpha_vantage>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tao-cli=cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
)
