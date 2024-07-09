#!/usr/bin/env python3

from setuptools import setup

setup(
	name = "iotc_ipc_dbus",
	version = "0.1.0",
	description = "Primitive Server/Client wrapper around pydbus Pythonic DBus library. Intented to be used for IOTC demos",
	author = "Vladislavas Putys",
	author_email = "vputys@witekio.com",
	url = "https://github.com/vputys/ipc_iotc_dbus",
	keywords = "dbus",
	license = "CLOSED",

	packages = ["iotc_ipc_dbus"],
	package_data = {"": ["LICENSE"]},
	package_dir = {"iotc_ipc_dbus": "iotc_ipc_dbus"},
	zip_safe = True,
	classifiers = [
		'Development Status :: 5 - Production/Stable',
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'License :: OSI Approved :: CLOSED',
		'Programming Language :: Python',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7'
	]
)
