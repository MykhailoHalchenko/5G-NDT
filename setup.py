from setuptools import setup, find_packages

setup(
    name="5g-ndt",
    version="0.1.0",
    description="5G Network Digital Twin for KAI Network lab",
    author="KAI Network Lab",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pytwinnet==0.1.3",
        "pydantic==2.4.2",
        "pydantic-settings==2.0.3",
        "neo4j==5.14.1",
        "influxdb-client==1.36.1",
        "kafka-python==2.0.2",
        "python-dotenv==1.0.0",
        "loguru==0.7.2",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-cov==4.1.0",
            "black",
            "flake8",
            "mypy",
        ]
    },
)
