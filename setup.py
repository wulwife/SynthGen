from setuptools import setup, find_packages


VERSION = "0.1.0"
AUTHORS = "[Francesco Grigoli, ]"
CONTACTS = "[francesco.grigoli@unipi.it, ]"

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required_list = f.read().splitlines()

setup(
    name="synthgen",
    version=VERSION,
    author=AUTHORS,
    author_email=CONTACTS,
    description="Synthetic seismic waveform generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wulwife/SynthGen",
    python_requires='>=3.9',
    install_requires=required_list,
    setup_requires=['wheel'],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: MacOS",
        "Intended Audience :: Science/Research",
    ],
    include_package_data=True,
    zip_safe=False,
    scripts=['bin/generate_synthetics.py', ])
