from setuptools import setup, find_packages

setup(
    name="tool-function",
    version="0.1.0",
    description="A collection of tool functions supporting AI Platform operations",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="CanhLD",
    author_email="ldcanh03042001@gmail.com",
    url="https://gitlab-data.vetc.com.vn/vetc-data-team/ai/ai-platform/tool-function.git",
    license="MIT",
    packages=find_packages(include=["tools", "tools.*", "utils", "utils.*", "variables", "variables.*", "plugins"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "pandas",
        "SQLAlchemy",
        "clickhouse-driver",
        "psycopg2-binary",
        "PyYAML",
        "loguru",
        "tqdm",
        "requests",
        "google-api-python-client",
        "google-auth"
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
            "isort",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ai-platform data-engineering connectors tools clickhouse postgres",
)
