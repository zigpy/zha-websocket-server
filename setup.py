"""Setup module for zha-websocket-server"""

import pathlib

from setuptools import find_packages, setup

setup(
    name="zhaws",
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
        "colorlog",
        "pydantic",
        "websockets",
        "voluptuous",
        "uvloop",
        "zigpy==0.43.0",
        "bellows==0.29.0",
        "zha-quirks==0.0.66",
        "zigpy-deconz==0.14.0",
        "zigpy-xbee==0.14.0",
        "zigpy-zigate==0.7.4",
        "zigpy-znp==0.7.0",
    ],
    package_data={"": ["appdb_schemas/schema_v*.sql"]},
)
