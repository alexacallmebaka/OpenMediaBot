import setuptools

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

setuptools.setup(
    name="OpenMediaBot",
    version="1.1.2",
    author="alexacallmebaka",
    license="Apache License 2.0",
    description="A library for creating media bots.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexacallmebaka/OpenMediaBot",
    project_urls={
        "Bug Tracker": "https://github.com/alexacallmebaka/OpenMediaBot/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable"
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    install_requires = [
        'pydrive2',
        'twython',
        'simplejson',
        'pillow'
    ],
    python_requires=">=3.7",
)