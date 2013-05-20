from re import search

def operation_wrapper(operation, *args):
    args = filter(lambda x : x != '', args)
    return operation(*args)

def is_in(value, array):
    return bool(value in array)

def is_not_in(value, array):
    return bool(value not in array)

def is_empty(record_field):
    return bool(not record_field)

def starts_with(needle, haystack):
    return bool(haystack.startswith(needle))

def ends_with(needle, haystack):
    return bool(haystack.endswith(needle))

def regex_match(value, pattern):
    try:
        found = search(str(pattern),value).group()
    except AttributeError:
        found = False
    return bool(found)