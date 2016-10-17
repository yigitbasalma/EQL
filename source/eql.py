#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, abort, make_response, request
from couchbase.bucket import Bucket

import LogMaster
import requests
import time
import os
import ConfigParser
import couchbase

import hashlib as h

class EQL(object):
	def __init__(self, watcher=False):
		self.logger = LogMaster.Logger()
		config = ConfigParser.ConfigParser()
		config.read("/EQL/source/config.cfg")
		if watcher:
			self.watcher_bucket = Bucket("couchbase://{0}/{1}".\
				format(config.get("env","cbhost"), config.get("env","watcher_bucket")))
		else:
			self.cache_bucket = Bucket("couchbase://{0}/{1}".\
                                format(config.get("env","cbhost"), config.get("env","cache_bucket")))
		self.own_ip = config.get("env","self_ip")
			
	def _is_cached(self, url):
		try:
			host = self.cache_bucket.get(h.md5(url).hexdigest()).value
			return (False, host)
		except couchbase.exceptions.NotFoundError:
			return (True, 1)

	def _cache_item(self, url):
		try:
			self.cache_bucket.insert(h.md5(url).hexdigest(), self.own_ip, ttl=604800)
		except couchbase.exceptions.KeyExistsError:
			pass

	def route_request(self, url):
		error, host = self._is_cached(url)
		if error:
			self._cache_item(url)
			return "error"
		else:
			return host

	def check_hosts(self):
		pass
