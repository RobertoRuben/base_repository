from setuptools import setup, find_packages

setup(
    name="base_repository",
    version="0.1.0",
    author="Roberto Ruben",
    author_email="tu@email.com",
    description="A SQL repository pattern implementation",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/RobertoRuben/base_repository",
    packages=find_packages(),
    install_requires=[
        "sqlmodel==0.0.22",
        "natsort==8.4.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)