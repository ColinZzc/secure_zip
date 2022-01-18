import time


def timer(func):
    def wrapper(*args, **kw):
        tic = time.time()
        return_data = func(*args, **kw)
        tok = time.time()
        print(f'{func.__name__} runs {tok-tic:.2f} seconds')
        return return_data
    return wrapper
