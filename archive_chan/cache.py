"""
    Implements caching.
"""


import re
import hashlib
from functools import wraps
from flask import request, Blueprint
from flask.ext.login import current_user
from werkzeug._compat import to_native
from werkzeug.contrib.cache import MemcachedCache, NullCache


cache = None


_test_memcached_key = re.compile(r'[^\x00-\x21\xff]{1,250}$').match
class PatchedMemcachedCache(MemcachedCache):
    """Stupid patch for python3-memcached. This will be fixed in the next
    wersion of Werkzeug. This code can be removed after its release.
    """

    def __init__(self, *args, **kwargs):
        super(PatchedMemcachedCache, self).__init__(*args, **kwargs)
        self.key_prefix = to_native(self.key_prefix)

    def _normalize_key(self, key):
        key = to_native(key, 'utf-8')
        if self.key_prefix:
            key = self.key_prefix + key
        return key

    def get(self, key):
        key = self._normalize_key(key)
        if _test_memcached_key(key):
            return self._client.get(key)

    def set(self, key, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        key = self._normalize_key(key)
        return self._client.set(key, value, timeout)


def init_app(app):
    """Call this to init this module with the preferred cache object."""
    global cache
    cache = get_preferred_cache_system(app)


def get_preferred_cache_system(app):
    """Returns an initialized cache object."""
    if app.config['MEMCACHED_URL']:
        return PatchedMemcachedCache(
            app.config['MEMCACHED_URL'],
            default_timeout=app.config['CACHE_TIMEOUT'],
            key_prefix='archive_chan'
        )
    return NullCache()


def get_md5(string):
    """Returns a hash of a string."""
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()


def get_cache_key(vary_on_auth):
    """Construct a cache key."""
    # Query url part matters in board view (catalog and the entire url can be
    # very long and may contain weird characters it is better to hash it).
    cache_key = get_md5(request.url)
    if vary_on_auth:
        cache_key += 'auth-%s' % current_user.is_authenticated()
    return cache_key


def cached(timeout=None, vary_on_auth=False):
    """Simple cache decorator taken from Flask docs.
    
    timeout: Cache timeout in seconds. Defaults to the default timeout set for
             the cache system if None.
    vary_on_auth: Indicates whether a different cache should be served to
                  authenticated users.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = get_cache_key(vary_on_auth)
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


class CachedBlueprint(Blueprint):
    """Blueprint which automatically adds cached decorator to all views added
    by add_url_rule method.

    timeout: See cached decorator.
    vary_on_auth: See cached decorator.
    default_cached: Indicates whether the views should be cached by default.
    """

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop('timeout', None)
        self.vary_on_auth = kwargs.pop('vary_on_auth', False)
        self.default_cached = kwargs.pop('default_cached', True)
        super(CachedBlueprint, self).__init__(*args, **kwargs)

    def add_url_rule(self, *args, **kwargs):
        """Exactly like add_url_rule but adds a cache decorator if desired.

        cached: Indicates whether the view should be cached. Defaults to 
                default_cached. Can be used to everride the default setting.
        """
        if kwargs.pop('cached', self.default_cached):
            kwargs['view_func'] = cached(
                timeout=self.timeout,
                vary_on_auth=self.vary_on_auth
            )(kwargs['view_func'])
        super(CachedBlueprint, self).add_url_rule(*args, **kwargs)
