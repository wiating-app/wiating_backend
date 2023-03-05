import logging

logger = logging.getLogger('myLogger')
logger.setLevel(logging.INFO)

# add handler to the logger
handler = logging.handlers.SysLogHandler('/dev/log')

# add syslog format to the handler
formatter = logging.Formatter(
    'Python: { "loggerName":"%(name)s", "timestamp":"%(asctime)s", "pathName":"%(pathname)s", "logRecordCreationTime":"'
    '%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "time":"%(msecs)d", '
    '"levelName":"%(levelname)s", "message":"%(message)s"}')

handler.formatter = formatter
logger.addHandler(handler)
