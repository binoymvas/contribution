import logging

# setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('brewer')
DESCRIPTION = "Brewer Tool"