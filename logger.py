import logging

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Logger(metaclass=Singleton):
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
        self.logger = logging.getLogger()

    def get_logger(self):
        return self.logger