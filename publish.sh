python setup.py sdist bdist_wheel
python -m twine upload --repository gitlab --skip-existing dist/* --verbose --cert C:\\Install\\caroot.crt
exec bash