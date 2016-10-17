#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, abort, make_response, request, send_file, Response
from source import eql, LogMaster
from werkzeug.routing import BaseConverter
import requests
import time
import os

app = Flask(__name__)
logger = LogMaster.Logger()
eql = eql.EQL()

class RegexConverter(BaseConverter):
        def __init__(self, url_map, *items):
                super(RegexConverter, self).__init__(url_map)
                self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

@app.route("/<regex('.*'):param>")
def cache(param):
	return eql.route_request(param)

@app.errorhandler(404)
def notfound_error(error):
	ip = request.headers.get("X-Real-IP")
        requestpath = request.path
	msg = '{0}, {1}, RESPONSE:404 NOT FOUND'.format(ip,requestpath)
        logger.LogSave('REST SERVICE','ACCESS',msg)
	return make_response(jsonify({'error': 'Aradiginiz endpoint bulunamadi yada artik sistemde yer almiyor.'}),\
		 404)

@app.errorhandler(500)
def internal_server_error(error):
    msg = 'Sunucu bir hata ile karsilasti.Lutfen loglari inceleyin.'
    logger.LogSave('REST SERVICE','CRITIC',msg)
    return make_response(jsonify({'error': 'Sistem yoneticinizle gorusun'}), 500)

if __name__ == '__main__':
        pidfile = "{0}/pid".format(os.path.dirname(os.path.realpath(__file__)))
        pid = str(os.getpid())
        if os.path.isfile(pidfile):
                os.unlink(pidfile)
        file(pidfile, 'w').write(pid)
        app.run("127.0.0.1", 5000, debug=True, threaded=True)
