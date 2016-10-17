#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser
import os
import datetime

class Logger(object):
	def __init__(self):
		config = ConfigParser.ConfigParser()
		config.read("/EQL/source/config.cfg")
		self.path = config.get("log","log_path")
		self.file_name = config.get("log","file_name")
		try:
			os.listdir(self.path)
		except OSError:
			os.mkdir(self.path,0755)
		self.path = "{0}/{1}.txt".format(self.path, self.file_name)

	def LogSave(self,scname,level,msg):
		self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		self.service_name = scname
		self.msg = msg
		self.level = level
		log_file = open(self.path,"a")
		self.log = "[{0}] [{1}] [{3}] [{2}]\n".format(str(self.timestamp),\
			 str(self.service_name), str(self.msg), str(self.level))
		log_file.write(self.log)
		log_file.close()
