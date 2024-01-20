import logging
import os
import sys
import traceback

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s: %(levelname)s, %(threadName)s, %(filename)s, %(funcName)s] %(message)s',
    handlers=[
        logging.FileHandler(f'{os.path.abspath(os.path.dirname(__file__))}/ezhov_bot.log', encoding='utf8'),
        logging.StreamHandler(sys.stdout)
    ]
)


def logging_uncaught_exceptions(ex_type, ex_value, trace_back):
    if issubclass(ex_type, KeyboardInterrupt):
        sys.__excepthook__(ex_type, ex_value, trace_back)
        return
    logging.critical(''.join(traceback.format_tb(trace_back)))
    logging.critical('{0}: {1}'.format(ex_type, ex_value))


sys.excepthook = logging_uncaught_exceptions

logger = logging.getLogger(__name__)


class FilterRepeatingBot(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return not (record.getMessage().endswith('Entering: get_updates')
                    or record.getMessage().endswith('Exiting: get_updates')
                    or record.getMessage().endswith('No new updates found.')
                    or record.getMessage().endswith('()')
                    or record.getMessage().endswith('Entering: send_message')
                    or record.getMessage().endswith('Exiting: send_message'))


class FilterRepeatingApplication(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return not (record.getMessage().endswith('Starting next run of updating the persistence.')
                    or record.getMessage().endswith('Finished updating persistence.'))


class FilterRepeatingClient(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return not (record.getMessage().endswith('"HTTP/1.1 200 OK"')
                    or record.getMessage().endswith('"HTTP/1.1 200 OK"'))


logging.getLogger('telegram._bot').addFilter(FilterRepeatingBot())
logging.getLogger('telegram.ext._application').addFilter(FilterRepeatingApplication())
logging.getLogger('httpx._client').addFilter(FilterRepeatingClient())
logging.getLogger('mtprotosender').setLevel(logging.INFO)

