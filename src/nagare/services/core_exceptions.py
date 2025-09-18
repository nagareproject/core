# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --


from webob import exc

from nagare.services import http_exceptions
from nagare.services.callbacks import CallbackLookupError


def exception_handler(exception, exceptions_service, request, **context):
    if isinstance(exception, CallbackLookupError):
        # As the XHR requests use the same continuation, a callback
        # can be not found (i.e deleted by a previous XHR)
        # In this case, do nothing
        if request.is_xhr:
            exceptions_service.logger.warning('Callback lookup error in XHR request')
            exception = exc.HTTPOk()
        else:
            exceptions_service.log_exception('nagare.services.callbacks')
            exception = exc.HTTPBadRequest('Invalid action identifier')

    return exception


class ExceptionsService(http_exceptions.ExceptionsService):
    LOAD_PRIORITY = http_exceptions.ExceptionsService.LOAD_PRIORITY + 2
    CONFIG_SPEC = dict(
        http_exceptions.ExceptionsService.CONFIG_SPEC,
        exception_handlers="""string_list(default=list(
            'nagare.services.core_exceptions:exception_handler',
            'nagare.services.http_exceptions:exception_handler',
            'nagare.services.http_exceptions:http_exception_handler'
        ))""",
    )
