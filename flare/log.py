# -*- coding: utf-8 -*-
import os, sys, threading, time, logging
from typing import Any
from js import console

# fixme: This is a little strange, global objects only work inside lists or dicts (Pyodide-related)
loggers = []


class FlareLogRecord(logging.LogRecord):
	"""
	A LogRecord instance represents an event being logged.

	LogRecord instances are created every time something is logged. They
	contain all the information pertinent to the event being logged. The
	main information passed in is in msg and args, which are combined
	using str(msg) % args to create the message field of the record. The
	record also includes information such as when the record was created,
	the source line where the logging call was made, and any exception
	information to be logged.

	NOTE: This is mostly the same as the original LogRecord but do not use
	a single dict as keyword args because pyodites' Proxy objects cannot be used
	with isinstance(proxy, collections.abc.Mapping).
	"""

	def __init__(self, name, level, pathname, lineno,
	             msg, args, exc_info, func=None, sinfo=None, **kwargs):
		"""
		Initialize a logging record with interesting information.
		"""
		#super().__init__()

		ct = time.time()
		self.name = name
		self.msg = msg
		#
		# The following statement allows passing of a dictionary as a sole
		# argument, so that you can do something like
		#  logging.debug("a %(a)d b %(b)s", {'a':1, 'b':2})
		# Suggested by Stefan Behnel.
		#
		# Note that without the test for args[0], we get a problem because
		# during formatting, we test to see if the arg is present using
		# 'if self.args:'. If the event being logged is e.g. 'Value is %d'
		# and if the passed arg fails 'if self.args:' then no formatting
		# is done. For example, logger.warning('Value is %d', 0) would log
		# 'Value is %d' instead of 'Value is 0'.
		# For the use case of passing a dictionary, this should not be a
		# problem.
		#
		# Issue #21172: a request was made to relax the isinstance check
		# to hasattr(args[0], '__getitem__'). However, the docs on string
		# formatting still seem to suggest a mapping object is required.
		# Thus, while not removing the isinstance check, it does now look
		# for collections.abc.Mapping rather than, as before, dict.
		self.args = args
		self.levelname = logging.getLevelName(level)
		self.levelno = level
		self.pathname = pathname
		try:
			self.filename = os.path.basename(pathname)
			self.module = os.path.splitext(self.filename)[0]
		except (TypeError, ValueError, AttributeError):
			self.filename = pathname
			self.module = "Unknown module"
		self.exc_info = exc_info
		self.exc_text = None  # used to cache the traceback text
		self.stack_info = sinfo
		self.lineno = lineno
		self.funcName = func
		self.created = ct
		self.msecs = (ct - int(ct)) * 1000
		self.relativeCreated = (self.created - logging._startTime) * 1000
		if logging.logThreads:
			self.thread = threading.get_ident()
			self.threadName = threading.current_thread().name
		else:  # pragma: no cover
			self.thread = None
			self.threadName = None
		if not logging.logMultiprocessing:  # pragma: no cover
			self.processName = None
		else:
			self.processName = 'MainProcess'
			mp = sys.modules.get('multiprocessing')
			if mp is not None:
				# Errors may occur if multiprocessing has not finished loading
				# yet - e.g. if a custom import hook causes third-party code
				# to run when multiprocessing calls import. See issue 8200
				# for an example
				try:
					self.processName = mp.current_process().name
				except Exception:  # pragma: no cover
					pass
		if logging.logProcesses and hasattr(os, 'getpid'):
			self.process = os.getpid()
		else:
			self.process = None


class JSConsoleHandler(logging.StreamHandler):
	"""
	Brings our awesome log messages onto the js console
	"""

	def emit(self, record: logging.LogRecord) -> None:
		msg = self.format(record)
		if record.levelno == logging.DEBUG:
			console.debug(msg, *record.args)
		elif record.levelno == logging.INFO:
			console.info(msg, *record.args)
		elif record.levelno == logging.WARNING:
			console.warn(msg, *record.args)
		elif record.levelno == logging.ERROR:
			if record.exc_info:
				console.error(msg, *record.args)
			else:
				myargs = ["color: red; font-weight: bold;"]
				myargs.extend(record.args)
				msg = "%c{0}".format(msg)
				console.log(msg, *myargs)
		elif record.levelno == logging.CRITICAL:
			console.error(msg, *record.args)
		else:
			console.log("Don't know which level", record.msg, *record.args)


def prepareLogger(level: str = None) -> None:
	"""
	Calls this before first usage of logging or getLogger()

	A good place would be on top level of the app to be logged.

	:param level Log level as str as of all, info, debug, warning, error or critical
	"""
	if loggers:
		return

	if level == "all":
		level = logging.NOTSET
	elif level == "info":
		level = logging.INFO
	elif level == "debug":
		level = logging.DEBUG
	elif level == "warning":
		level = logging.WARNING
	elif level == "error":
		level = logging.ERROR
	elif level == "critical":
		level = logging.CRITICAL
	else:
		level = logging.DEBUG


	logging.setLogRecordFactory(FlareLogRecord)
	logger = logging.getLogger()
	logger.setLevel(level)

	if level == logging.NOTSET:
		# Enable fully fledged drill-down debug in JS console
		# This results in double lines currently.
		ch = JSConsoleHandler()
		ch.setLevel(level)
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s')
		ch.setFormatter(formatter)
		logger.addHandler(ch)

	loggers.append(logger)


def getLogger(name: str) -> Any:
	"""
	Creates a child logger of our 'root' logger with a name.

	Usually it's the __name__ attribute of the module you want to use a logger for.

	:param name:
	:return:
	"""

	return loggers[0].getChild(name)
