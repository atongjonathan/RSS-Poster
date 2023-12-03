from logging import getLogger, basicConfig, INFO, StreamHandler, FileHandler

basicConfig(
    format="%(asctime)s | %(levelname)s | %(module)s - line_no %(lineno)s : %(message)s ",
    handlers=[
        StreamHandler(),
        FileHandler('./logs.txt')],
    level=INFO)
LOGGER = getLogger(__name__)
