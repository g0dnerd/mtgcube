import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class SessionMiddlewareDynamicDomain(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)

    def process_response(self, request, response):
        if settings.SESSION_COOKIE_NAME in response.cookies:
            try:
                domain_curr = response.cookies[settings.SESSION_COOKIE_NAME]['domain']

                request_domain = '.' + '.'.join(request.get_host().split(':')[0].split('.')[-2:])

                if request_domain in settings.SESSION_COOKIE_DOMAIN_DYNAMIC:
                    if domain_curr != request_domain:
                        response.cookies[settings.SESSION_COOKIE_NAME]['domain'] = request_domain
            except Exception as exc:
                logging.error(f'crash updating domain dynamically. Skipped. Error: {exc}')

        return response