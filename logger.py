import logging
import uuid
from pythonjsonlogger import jsonlogger

runID = str(uuid.uuid4())
class UUIDFilter(logging.Filter):
    def filter(self, record):
        record.runID = runID
        return True

LOGFILE = '/mnt/gfycat_bot/gfycat_bot.log'
logHandler = logging.FileHandler(filename=LOGFILE)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(runID)s %(message)s')
logHandler.setFormatter(formatter)
logging.getLogger().addHandler(logHandler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()
logger.addFilter(UUIDFilter())
