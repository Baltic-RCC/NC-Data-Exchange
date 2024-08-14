python setup.py sdist bdist_wheel
python -m twine upload --repository gitlab-nc-data-exchange --skip-existing dist/* --verbose --cert C:\\Install\\caroot.crt
exec bash