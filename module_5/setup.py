from setuptools import find_packages, setup

setup(
    name="gradcafe-analytics",
    version="0.1.0",
    description="Module 5: Hardened Flask + PostgreSQL analytics app",
    package_dir={"": "."},
    packages=find_packages(where="."),
    include_package_data=True,
    install_requires=[
        "Flask>=3.0.0",
        "psycopg[binary]>=3.1.18",
        "python-dotenv>=1.0.1",
    ],
)
