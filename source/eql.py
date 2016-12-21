#!/usr/bin/python
# -*- coding: utf-8 -*-

from couchbase.bucket import Bucket
from multiprocessing import Process

import requests
import datetime
import ConfigParser
import couchbase
import sqlite3
import time

import hashlib as h


class Db(object):
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.vt = self.conn.cursor()

    def write(self, query):
        self.vt.execute(query)
        self.conn.commit()
        return True

    def count(self, query):
        self.vt.execute(query)
        return self.vt.rowcount

    def readt(self, query):
        self.vt.execute(query)
        return self.vt.fetchall()


class EQL(Db):
    def __init__(self, logger, watcher=False, clustered=False, with_static=False):
        self.logger = logger
        self.config = ConfigParser.ConfigParser()
        self.config.read("/EQL/source/config.cfg")
        self.cache_bucket = Bucket("couchbase://{0}/{1}".\
                                   format(self.config.get("env", "cbhost"), self.config.get("env", "cache_bucket")), lockmode=2)
        self.statistic_bucket = Bucket("couchbase://{0}/{1}".\
                                       format(self.config.get("env", "cbhost"),
                                              self.config.get("env", "statistic_bucket")), lockmode=2)
        self.server = self.config.get("env", "server")
        self.clustered = clustered
        self.timeout = float(self.config.get("env", "timeout"))
        if clustered:
            Db.__init__(self)
            self.write("CREATE TABLE lb(HOST VARCHAR(100) PRIMARY KEY, STATUS VARCHAR(20), WEIGHT INT(3) DEFAULT '0')")
            self.clustered = True
            self._health_check_cluster(first=True)
        if with_static:
            self.mime_type = {
                "css": "text/css",
                "js": "application/javascript"
            }
            self.root_directory = str(self.config.get("env", "root_directory"))
        if watcher:
            check_interval = int(self.config.get("env", "check_interval"))
            p = Process(target=self._health_check_cluster, name="EQL_Watcher", kwargs={"check_interval":check_interval})
            p.start()

    def _health_check_cluster(self, first=False, check_interval=3):
        if first:
            cluster = self.config.get("env", "cluster").split(",")
            cluster.append(self.server)
            url = self.config.get("env", "health_check_url")
            weight = 1
            for server in cluster:
                status = None
                try:
                    req = requests.get("http://{0}{1}".format(server, url), timeout=self.timeout)
                    status = "up" if req.status_code == 200 else "down"
                except requests.exceptions.Timeout:
                    status = "down"
                except requests.exceptions.ConnectionError:
                    status = "down"
                finally:
                    if status == "down":
                        self.logger.log_save("EQL", "ERROR", "{0} Sunucusu down.".format(server))
                    self.write("INSERT INTO lb VALUES ('{0}', '{1}', '{2}')".format(server, status, weight))
                    weight += 1
            return True
            
        while True:
            #config = ConfigParser.ConfigParser()
            #config.read("/EQL/source/config.cfg")
            #cluster = config.get("env", "cluster").split(",")
            cluster = [i[0] for i in self.db.readt("SELECT HOST FROM lb")]
            url = config.get("env", "health_check_url")
            weight = 1
            for server in cluster:
                status = None
                try:
                    req = requests.get("http://{0}{1}".format(server, url), timeout=self.timeout)
                    status = "up" if req.status_code == 200 else "down"
                except requests.exceptions.Timeout:
                    status = "down"
                except requests.exceptions.ConnectionError:
                    status = "down"
                finally:
                    try:
                        if status == "down":
                            self.logger.log_save("EQL", "ERROR", "{0} Sunucusu down.".format(server))
                        self.write("INSERT INTO lb VALUES ('{0}', '{1}', '{2}')".format(server, status, weight))
                    except sqlite3.IntegrityError:
                        self.write("UPDATE lb SET STATUS='{0}', WEIGHT='{1}' WHERE HOST='{2}'".format(status, weight, server))
                    weight += 1
            time.sleep(int(check_interval))

    def _is_cached(self, url):
        urls = h.md5(url).hexdigest()
        try:
            values = self.cache_bucket.get(urls).value
            type_ = self._statistic(urls, r_turn=True)
            if type_ is None:
                raise ValueError()
            return True, values, type_
        except (couchbase.exceptions.NotFoundError, ValueError):
            try:
                req = requests.get("http://{0}{1}".format(self.server, url), timeout=self.timeout)
            except requests.exceptions.Timeout:
                if not self.clustered:
                    self.logger.log_save("EQL", "CRITIC", "Backend server timeout hatası aldı.")
                    return False, int(500)
                while True:
                    pool = self._get_server()
                    try:
                        try:
                            self.server = pool.next()
                            req = requests.get("http://{0}{1}".format(self.server, url), timeout=self.timeout)
                            if req.status_code == 200: break
                        except:
                            pass
                    except StopIteration:
                        self.logger.log_save("EQL", "CRITIC", "Tüm backend serverlar timeout hatası aldı.")
                        return False, int(500)
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

    def _statistic(self, url, type_=None, r_turn=False):
        try:
            values = self.statistic_bucket.get(url).value
            count, timestamp, type_ = values[0], values[1], values[2]
            count += 1
            obj = [count, timestamp, type_]
            self.statistic_bucket.replace(url, obj)
        except couchbase.exceptions.NotFoundError:
            if r_turn:
                if type_ is None:
                    return False
            count = 1
            obj = [count, datetime.datetime.now().strftime("%Y-%m-%d %H:%I:%S"), type_]
            self.statistic_bucket.insert(url, obj)
        finally:
            if r_turn:
                return type_
            return True

    def _get_server(self):
        cluster = self.readt("SELECT HOST,WEIGHT FROM lb WHERE STATUS='up' ORDER BY WEIGHT ASC")
        itr = 1
        while len(cluster) >= itr:
            yield cluster[itr - 1][0]
            itr += 1

    def route_request(self, url, from_file=False):
        # return status, data, mime type
        if from_file:
            urls = h.md5(url).hexdigest()
            try:
                values = self.cache_bucket.get(urls).value
                type_ = self._statistic(urls, r_turn=True)
                return True, values, type_
            except couchbase.exceptions.NotFoundError:
                try:
                    file_ = open(self.root_directory + str(url))
                except IOError:
                    return False, int(500)
                data = file_.read()
                type_ = self.mime_type[url.split(".")[-1]]
                self._cache_item(urls, data)
                self._statistic(urls, type_)
                return True, data, type_

        return self._is_cached(url)
