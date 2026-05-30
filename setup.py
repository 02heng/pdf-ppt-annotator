from setuptools import setup, find_packages

setup(
    name="pdf-ppt-annotator",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "crewai>=1.14.0",
        "customtkinter>=5.2.0",
        "PyMuPDF>=1.23.0",
        "python-pptx>=0.6.21",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "cryptography>=41.0.0",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pdf-annotator=src.main:main",
        ],
    },
)
