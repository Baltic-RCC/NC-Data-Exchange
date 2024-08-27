import setuptools

setuptools.setup(
    name="nc-data-exchange",
    version="0.0.2",
    author="Martynas Karobcikas",
    author_email="martynas.karobcikas@baltic-rcc.eu",
    description="A package for building NetworkCode data exchange profiles",
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
        "pandas>=2.2.2",
        "pydantic>=2.5.2",
        "lxml>=5.0.0",
        "rdflib>=7.0.0",
        "triplets>=0.0.7",
        "pyshacl>=0.26.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    include_package_data=True,
)
