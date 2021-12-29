"""Setup module for zha-websocket-server"""

import pathlib

from setuptools import find_packages, setup

import zhawss

setup(
    name="zhawss",
    version="2021.12.0",
    description="Library implementing a Zigbee websocket server",
    long_description=(pathlib.Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/zigpy/zha-websocket-server",
    author="David F. Mulcahey",
    author_email="david.mulcahey@icloud.com",
    license="GPL-3.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "websockets",
        "voluptuous",
        "zigpy>=0.42.0",
    ],
    package_data={"": ["appdb_schemas/schema_v*.sql"]},
)
