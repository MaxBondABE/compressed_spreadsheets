from setuptools import setup
import pathlib

import compressed_spreadsheets

here = pathlib.Path(__file__).parent.resolve()

setup(
    name="compressed_spreadsheets",
    version=compressed_spreadsheets.__version__,
    description="Read & write to gzip compressed CSV files.",
    long_description=(here/"README.md").read_text(encoding="utf-8"),
    long_description_content_type='text/markdown',
    url="https://github.com/MaxBondABE/compressed_spreadsheets",
    author="Max Bond",
    keywords="compressed, csv",
    python_requires=">=3.5, <4",
    py_modules=["compressed_spreadsheets"],
    extras_requires={
        "dev": ["hypothesis", "pytest"]
    }
)
