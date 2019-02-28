import logging
import uuid
from pythonjsonlogger import jsonlogger

extra={'runID': str(uuid.uuid4())}
LOGFILE = '/mnt/gfycat_bot/gfycat_bot.log'
logHandler = logging.FileHandler(filename=LOGFILE)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(runID)s %(message)s')
logHandler.setFormatter(formatter)
logging.getLogger().addHandler(logHandler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()
