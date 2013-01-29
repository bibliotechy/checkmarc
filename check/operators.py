import operator



def _operation_function(check):
    operator_functions ={
        u'eq' : operator.eq,
        u'nq' : operator.ne,
        u'ex' : operator.truth,
        u'nx' : operator.not_,
        u'cn' : _is_in,
        u'dc' : _is_not_in,
        u'em' : _is_empty,
        u'sw' : _starts_with,
        u'ew' : _ends_with
    }
    return operator_functions[check.operator]


def _is_in(value, array):
    return bool(value in array)

def _is_not_in(value, array):
    return bool(value not in array)

def _is_empty(record_field):
    return bool(record_field)

def _starts_with(needle, haystack):
    return bool(haystack.startswith(needle))

def _ends_with(needle, haystack):
    return bool(haystack.endswith(needle))


def _response_builder(record, check):

    response = _run_operation(record, check)
    return response

def _run_operation(record, check):
    operation = _operation_function(check)
    if _leader(check):
        if _operation_wrapper(operation, record.leader[check.leader], check.values):
            return check
    if _field(check):
        if _operation_wrapper(operation, record[check.field], check.values):
            return check
    if _subfield(check):
        if _operation_wrapper(operation, record[check.field][check.subfield], check.values):
            return check
    if _indicator(check):
        if _operation_wrapper(operation, record[check.field].indicators[int(check.indicator)], check.values ):
            return check

def _operation_wrapper(operation, record_value, check_value):
    return operation(record_value, check_value)


def _leader(check):
    return bool(check.leader)

def _field(check):
    return bool(not check.subfield and not check.indicator)

def _subfield(check):
    return bool(check.subfield and not check.indicator)

def _indicator(check):
    return bool(check.indicator and not check.subfield)


