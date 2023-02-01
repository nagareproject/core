# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --


from nagare.services import http_exceptions
from nagare.services.callbacks import CallbackLookupError
from webob import exc


def default_exception_handler(exception, exceptions_service, services_service, request, **context):
    if isinstance(exception, CallbackLookupError):
        # As the XHR requests use the same continuation, a callback
        # can be not found (i.e deleted by a previous XHR)
        # In this case, do nothing
        if request.is_xhr:
            exceptions_service.logger.warning('Callback lookup error in XHR request')
            exception = exc.HTTPOk()
        else:
            exceptions_service.log_exception('nagare.callbacks')
            exception = exc.HTTPInternalServerError()

    if isinstance(exception, exc.HTTPOk):
        return exception

    if not isinstance(exception, exc.HTTPException):
        exceptions_service.log_exception()
        exception = exc.HTTPInternalServerError()

    exception = services_service(exceptions_service.handle_exception, exception, request=request, **context)

    if getattr(exception, 'commit_transaction', False):
        return exception
    else:
        raise exception


class ExceptionsService(http_exceptions.ExceptionsService):
    LOAD_PRIORITY = http_exceptions.ExceptionsService.LOAD_PRIORITY + 2
    CONFIG_SPEC = dict(
        http_exceptions.ExceptionsService.CONFIG_SPEC,
        exception_handler='string(default="nagare.services.core_exceptions:default_exception_handler")',
    )
