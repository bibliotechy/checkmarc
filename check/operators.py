import operator

def _response_builder(record, check):

    if _run_operation(record, check):
        return check
    else:
        return ""

def _run_operation(record, check):
    operation = _operation_function(check)
    if _leader(check):
        return _operation_wrapper(operation, record.leader[check.leader], check.values)
    if _field(check):
        return _operation_wrapper(operation, record[check.field], check.values)
    if _subfield(check):
        return _operation_wrapper(operation, record[check.field][check.subfield], check.values)
    if _indicator(check):
        return _operation_wrapper(operation, record[check.field].indicators[int(check.indicator)], check.values )

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

def _leader(check):
    return bool(check.leader)

def _field(check):
    return bool(not check.subfield and not check.indicator)

def _subfield(check):
    return bool(check.subfield and not check.indicator)

def _indicator(check):
    return bool(check.indicator and not check.subfield)

def _operation_wrapper(operation, record_value, check_value):
    return operation(record_value, check_value)

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
