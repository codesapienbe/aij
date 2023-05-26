#!/usr/bin/env bash
echo "the project is being built for production..."
rm -rf dist
# print the previous version number
echo "The previous version number was: $(awk -F= '/^version = / {print $2}' pyproject.toml)"
# read from the user new version number
read -p "Enter the new version number: " version
# update the version number in the pyproject.toml file
sed -i "s/version = .*/version = \"$version\"/g" pyproject.toml
python -m build
py -m twine upload --repository pypi dist/*
echo "the project is succesfully built"
echo "The package has been published to PyPI."
