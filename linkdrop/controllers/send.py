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
import datetime
import json
import urllib
import sys
import httplib2
import copy
from urlparse import urlparse
from paste.deploy.converters import asbool
import hashlib

from pylons import config, request, response
from pylons.controllers.util import abort, redirect
from pylons.decorators.util import get_pylons

from linkdrop.lib.base import BaseController
from linkdrop.lib.helpers import json_exception_response, api_response, api_entry, api_arg
from linkdrop.lib import constants
from linkdrop.lib.metrics import metrics

from linkdrop.lib.queue import get_queue_dispatcher

log = logging.getLogger(__name__)


class SendController(BaseController):
    """
Send
====

The 'send' namespace is used to send updates to our supported services.

"""
    __api_controller__ = True # for docs

    @api_response
    @json_exception_response
    @api_entry(
        doc="""
send
----

Share a link through F1.
""",
        queryargs=[
            # name, type, required, default, allowed, doc
            api_arg('domain', 'string', True, None, None, """
Domain of service to share to (google.com for gmail, facebook.com, twitter.com)
"""),
            api_arg('message', 'string', True, None, None, """
Message entered by user
"""),
            api_arg('username', 'string', False, None, None, """
Optional username, required if more than one account is configured for a domain.
"""),
            api_arg('userid', 'string', False, None, None, """
Optional userid, required if more than one account is configured for a domain.
"""),
            api_arg('link', 'string', False, None, None, """
URL to share
"""),
            api_arg('shorturl', 'string', False, None, None, """
Shortened version of URL to share
"""),
            api_arg('shorten', 'boolean', False, None, None, """
Force a shortening of the URL provided
"""),
            api_arg('to', 'string', False, None, None, """
Individual or group to share with, not supported by all services.
"""),
            api_arg('subject', 'string', False, None, None, """
Subject line for emails, not supported by all services.
"""),
            api_arg('picture', 'string', False, None, None, """
URL to publicly available thumbnail, not supported by all services.
"""),
            api_arg('picture_base64', 'string', False, None, None, """
Base 64 encoded PNG version of the picture used for attaching to emails.
"""),
            api_arg('description', 'string', False, None, None, """
Site provided description of the shared item, not supported by all services.
"""),
            api_arg('name', 'string', False, None, None, """
"""),
        ],
        response={'type': 'list', 'doc': 'raw data list'}
    )
    def send(self):
        # requried post data: domain, message, username or userid, link, account        
        required = ['domain']
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

        queue = get_queue_dispatcher()
        result, error = queue.process('send', data)
        if error and error['status'] == 202:
            result, error = queue.retreive(error['id'])

        return {'result': result, 'error': error}

