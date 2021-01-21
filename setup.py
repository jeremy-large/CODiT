"""
Python setuptools config to package this repository.
"""
from setuptools import setup, find_namespace_packages
from pathlib import Path

setup(
    name="codit",
    version="1.0.1",
    package_dir={"": "lib"},
    packages=find_namespace_packages(where="lib"),
    data_files=[(dir, [str(fn) for fn in Path(dir).glob("*") if fn.is_file()]) for dir in Path("share").glob("**/*") if dir.is_dir()],
    scripts=[str(fn) for fn in Path("scripts").glob("**/*") if fn.is_file()],
    include_package_data=True,
    zip_safe=False,
)
