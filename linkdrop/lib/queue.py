import json
import hashlib
import uuid

from linkoauth import get_provider
from linkoauth.util import asbool
from linkoauth.base import OAuthKeysException, ServiceUnavailableException

from linkdrop.lib import constants
from linkdrop.lib.shortener import shorten_link
from linkdrop.lib.metrics import metrics


class SendWorker(object):
        
    def process(self, data):
        account_data = data.get('account', None)
        message = data.get('message', '')
        domain = data.get('domain', '')
        username = data.get('username')
        userid = data.get('userid')
        longurl = data.get('link')
        shorten = asbool(data.get('shorten', 0))
        shorturl = data.get('shorturl')
        acct = json.loads(account_data)
        provider = get_provider(domain)
        if provider is None:
            error = {
                'message': "'domain' is invalid",
                'code': constants.INVALID_PARAMS
            }
            return None, error

        acct_hash = hashlib.sha1("%s#%s" % ((username or '').encode('utf-8'),
                                (userid or '').encode('utf-8'))).hexdigest()
        #timer = metrics.start_timer(None, domain=domain,
        #                            message_len=len(message),
        #                            long_url=longurl,
        #                            short_url=shorturl, acct_id=acct_hash)

        if shorten and not shorturl and longurl:
            #link_timer = metrics.start_timer(None, long_url=longurl)
            u = urlparse(longurl)
            if not u.scheme:
                longurl = 'http://' + longurl
            shorturl = shorten_link(longurl)
            #link_timer.track('link-shorten', short_url=shorturl)
            args['shorturl'] = shorturl

        try:
            try:
                result, error = provider.api(acct).sendmessage(message, data)
                
                if result:
                    # these are here to pass tests, probably are not used in the
                    # web client
                    result['shorturl'] = shorturl
                    result['from'] = userid
                    result['to'] = data.get('to')
                
                return result, error
            finally:
                pass
                #timer.track('send-success')
        except OAuthKeysException, e:
            # XXX - I doubt we really want a full exception logged here?
            #log.exception('error providing item to %s: %s', domain, e)
            # XXX we need to handle this better, but if for some reason the
            # oauth values are bad we will get a ValueError raised
            error = {'provider': domain,
                     'message': "not logged in or no user account for that domain",
                     'status': 401
            }

            #metrics.track(None, 'send-oauth-keys-missing', domain=domain)
            #timer.track('send-error', error=error)
            return None, error
        except ServiceUnavailableException, e:
            error = {'provider': domain,
                     'message': "The service is temporarily unavailable - please try again later.",
                     'status': 503
            }
            if e.debug_message:
                error['debug_message'] = e.debug_message
            #metrics.track(None, 'send-service-unavailable', domain=domain)
            #timer.track('send-error', error=error)
            return None, error


class ContactsWorker(object):
        
    def process(self, data):
        domain = data.get('domain', '')
        username = data.get('username')
        userid = data.get('userid')
        group = data.get('group', None)
        startIndex = int(data.get('startindex','0'))
        maxResults = int(data.get('maxresults','25'))
        account_data = data.get('account', None)
        provider = get_provider(domain)
        if provider is None:
            error = {
                'message': "'domain' is invalid",
                'code': constants.INVALID_PARAMS
            }
            return None, error

        acct = None
        if account_data:
            acct = json.loads(account_data)
        if not acct:
            #metrics.track(request, 'contacts-noaccount', domain=domain)
            error = {'provider': domain,
                     'message': "not logged in or no user account for that domain",
                     'status': 401
            }
            return None, error

        try:
            return provider.api(acct).getcontacts(startIndex, maxResults, group)
        except OAuthKeysException, e:
            # more than likely we're missing oauth tokens for some reason.
            error = {'provider': domain,
                     'message': "not logged in or no user account for that domain",
                     'status': 401
            }
            #metrics.track(request, 'contacts-oauth-keys-missing', domain=domain)
            return None, error
        except ServiceUnavailableException, e:
            error = {'provider': domain,
                     'message': "The service is temporarily unavailable - please try again later.",
                     'status': 503
            }
            if e.debug_message:
                error['debug_message'] = e.debug_message
            result = None
            #metrics.track(request, 'contacts-service-unavailable', domain=domain)
            return None, error


class SyncQueue(object):
    def process(self, action, data):
        if action == 'send':
            worker = SendWorker()
        elif action == 'contacts':
            worker = ContactsWorker()
        return worker.process(data)

    def retreive(self):
        raise Exception('are you nuts?')


# XXX rough notes, this is a fake async queue to test out retreival of the
# job results
class AsyncQueue(object):
    _queue = {}
    def process(self, action, data):
        # pretend we've sent it off to be done
        id = uuid.uuid4()
        self._queue[id] = (action,data)
        return None, {'status': 202,
                      'id': id,
                      'message': 'job accepted'}
    
    def retreive(self, id):
        # result is being retrieved now, we just do a sync process to get that
        # result.
        action, data = self._queue[id]
        del self._queue[id]
        if action == 'send':
            worker = SendWorker()
        elif action == 'contacts':
            worker = ContactsWorker()
        return worker.process(data)


def get_queue_dispatcher():
    return AsyncQueue()
