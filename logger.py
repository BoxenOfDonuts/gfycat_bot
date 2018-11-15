import logging
from pythonjsonlogger import jsonlogger

LOGFILE = '/mnt/gfycat_bot/gfycat_bot.log'
logHandler = logging.FileHandler(filename=LOGFILE)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(message)s')
logHandler.setFormatter(formatter)
logging.getLogger().addHandler(logHandler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()
