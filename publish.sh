python setup.py sdist bdist_wheel
python -m twine upload --repository-url https://artifactory.elering.sise:443/artifactory/api/pypi/rcc-pypi-local dist/* --cert C:\\Install\\caroot.crt
exec bash