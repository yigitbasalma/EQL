#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, abort, make_response, request, send_file, Response
from source import eql, LogMaster
from werkzeug.routing import BaseConverter


app = Flask(__name__)
logger = LogMaster.Logger("REST_SERVICE", "/EQL/source/config.cfg")
eql = eql.EQL(logger)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


@app.route("/<regex('.*'):param>")
def cache(param):
    rsp = eql.route_request(param)
    if rsp[0]:
        return Response(rsp[1], mimetype=rsp[2])
    else:
        abort(rsp[1])
        
        
@app.route("/static<regex('.*'):param>")
def cache_(param):
    rsp = eql.route_request("/static" + param)
    if rsp[0]:
        return Response(rsp[1], mimetype=rsp[2])
    else:
        abort(rsp[1])
        

@app.errorhandler(404)
def notfound_error(error):
    ip = request.headers.get("X-Real-IP")
    requestpath = request.path
    msg = '{0}, {1}, RESPONSE:404 NOT FOUND'.format(ip, requestpath)
    logger.log_save('REST SERVICE', 'ACCESS', msg)
    return make_response(jsonify({'error': 'Aradiginiz imaj bulunamadi..'}), 404)


@app.errorhandler(500)
def internal_server_error(error):
    requestpath = request.path
    msg = 'Sunucu bir hata ile karsilasti.Lutfen loglari inceleyin.URL : {0}'.format(requestpath)
    logger.log_save('REST SERVICE', 'CRITIC', msg)
    return make_response(jsonify({'error': 'Sistem yoneticinizle gorusun'}), 500)


if __name__ == '__main__':
    app.run("127.0.0.1", 5000, debug=True, threaded=True)
