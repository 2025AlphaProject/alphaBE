import sys

def get_my_function(depth=1):
    return sys._getframe(depth).f_code.co_name

def get_error_line(depth=1):
    return sys._getframe(depth).f_lineno

class ExceptionHandler(Exception):

    def __init__(self, error_func, error_line, error_code, error_message):
        self.error_func = error_func
        self.error_line = error_line
        self.error_code = error_code
        self.error_message = error_message

    def __str__(self):
        return f"error_func: {self.error_func},\
                 error_line: {self.error_line},\
                 error_code: {self.error_code},\
                 error_message: {self.error_message}"

