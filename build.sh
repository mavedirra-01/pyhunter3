#!/bin/bash
# Start fresh
rm -rf dist build *.egg-info

# Build the package
python3 setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*