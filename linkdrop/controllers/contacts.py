# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Raindrop.
#
# The Initial Developer of the Original Code is
# Mozilla Messaging, Inc..
# Portions created by the Initial Developer are Copyright (C) 2009
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#

import logging
import urllib, cgi, json, sys
from urlparse import urlparse
import copy

from pylons import config, request, response, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators import jsonify
from pylons.decorators.util import get_pylons

from linkoauth import get_provider
from linkoauth.base import OAuthKeysException, ServiceUnavailableException

from linkdrop.lib.base import BaseController, render
from linkdrop.lib.helpers import json_exception_response, api_response, api_entry, api_arg
from linkdrop.lib import constants
from linkdrop.lib.metrics import metrics

from linkdrop.lib.queue import get_queue_dispatcher

log = logging.getLogger(__name__)

class ContactsController(BaseController):
    """
Contacts
========

A proxy for retrieving contacts from a service.

"""
    __api_controller__ = True # for docs


    @api_response
    @json_exception_response
    @api_entry(
        doc="""
contacts
--------

Get contacts from a service.
""",
        urlargs=[
            api_arg('domain', 'string', True, None, None, """
The domain of the service to get contacts from (e.g. google.com)
"""),
        ],
        queryargs=[
            # name, type, required, default, allowed, doc
            api_arg('username', 'string', False, None, None, """
The user name used by the service. The username or userid is required if more
than one account is setup for the service.
"""),
            api_arg('userid', 'string', False, None, None, """
The user id used by the service. The username or userid is required if more
than one account is setup for the service.
"""),
            api_arg('startindex', 'integer', False, 0, None, """
Start index used for paging results.
"""),
            api_arg('maxresults', 'integer', False, 25, None, """
Max results to be returned per request, used with startindex for paging.
"""),
            api_arg('group', 'string', False, 'Contacts', None, """
Name of the group to return.
"""),
        ],
        response={'type': 'object', 'doc': 'Portable Contacts Collection'}
    )
    def get(self, domain):
        # requried post data: domain, ...
        required = []
        for key in required:
            if request.POST.get(key, None) is None:
                error = {
                    'message': "required argument '%s' is not optional" % key,
                    'code': constants.INVALID_PARAMS }
                return {'result': None, 'error': error}

        # validate, somewhat, the account data
        acct = None
        account_data = request.POST.get('account', None)
        if account_data:
            acct = json.loads(account_data)
        if not acct:
            error = {'provider': request.POST.get('domain'),
                     'message': "not logged in or no user account for that domain",
                     'status': 401 }
            return {'result': None, 'error': error}

        data = copy.copy(request.POST)
        data['domain'] = domain

        queue = get_queue_dispatcher()
        result, error = queue.process('contacts', data)
        if error and error['status'] == 202:
            result, error = queue.retreive(error['id'])

        return {'result': result, 'error': error}
