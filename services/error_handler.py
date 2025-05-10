import sys

def get_my_function(depth=1):
    return sys._getframe(depth).f_code.co_name

def get_error_line(depth=1):
    return sys._getframe(depth).f_lineno