import logging
import logging.handlers

LOG_FORMAT = "%(asctime)s %(levelname)s %(module)s[%(funcName)s:%(lineno)d]: %(message)s"


class ABLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name=name, level=level)

        # stderr
        formatter = logging.Formatter(LOG_FORMAT)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        self.addHandler(handler)


log = ABLogger(__name__, logging.DEBUG)
