#!/usr/bin/python
# -*- coding: utf-8 -*-

from couchbase.bucket import Bucket

import requests
import datetime
import os
import ConfigParser
import couchbase

import hashlib as h


class EQL(object):
    def __init__(self, logger, watcher=False):
        self.logger = logger
        config = ConfigParser.ConfigParser()
        config.read("/EQL/source/config.cfg")
        if watcher:
            self.watcher_bucket = Bucket("couchbase://{0}/{1}".\
                                         format(config.get("env", "cbhost"), config.get("env", "watcher_bucket")))
        self.cache_bucket = Bucket("couchbase://{0}/{1}".\
                                       format(config.get("env", "cbhost"), config.get("env", "cache_bucket")))
        self.statistic_bucket = Bucket("couchbase://{0}/{1}".\
                                       format(config.get("env", "cbhost"), config.get("env", "statistic_bucket")))
        self.own_ip = config.get("env", "self_ip")
        
    def _is_cached(self, url):
        urls = h.md5(url).hexdigest()
        try:
            values = self.cache_bucket.get(urls).value
            type = self._statistic(urls, r_turn=True)
            return True, values, type
        except couchbase.exceptions.NotFoundError:
            # Requests icin timeout exception hazirla
            req = requests.get("http://cdn1.n11.com.tr/{0}".format(url))
            if req.status_code == 200:
                self._cache_item(urls, req.content)
                self._statistic(urls, req.headers.get('content-type'))
                return True, req.content, req.headers.get('content-type')
            else:
                return False, int(req.status_code)

    def _cache_item(self, url, img):
        try:
            self.cache_bucket.insert(url, img, format=couchbase.FMT_BYTES)
        except couchbase.exceptions.KeyExistsError:
            pass
        finally:
            return True
            
    def _statistic(self, url, type=None, r_turn=False):
        try:
            values = self.statistic_bucket.get(url).value
            count, timestamp, type = values[0], values[1], values[2]
            count += 1
            obj = [count, timestamp, type]
            self.statistic_bucket.replace(url, obj)
        except couchbase.exceptions.NotFoundError:
            count = 1
            obj = [count, datetime.datetime.now().strftime("%Y-%m-%d %H:%I:%S"), type]
            self.statistic_bucket.insert(url, obj)
        finally:
            if r_turn:
                return type
            return True
            
        
    def route_request(self, url):
        return self._is_cached(url)