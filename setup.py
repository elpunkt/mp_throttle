import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mp_throttle",
    version="0.0.1",
    author="Lucas Langholf",
    author_email="lucas@elpunkt.eu",
    description="Package to monitor and throttle multiprocessing processes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elpunkt/mp_throttle",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: MIT License",
    ),
)
