import setuptools
import re
import os

def find_version_author_mail():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "mp_throttle/__init__.py"), 'r') as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    author_match = re.search(r"^__author__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    author, mail = re.split(r'<',author_match.group(1))
    return version_match.group(1), author.rstrip(), re.sub('>', '', mail)

version, author, mail = find_version_author_mail()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mp_throttle",
    version=version,
    author=author,
    author_email= mail,
    description="Package to monitor and throttle multiple processes or threads.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elpunkt/mp_throttle",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers"
    ),
)
