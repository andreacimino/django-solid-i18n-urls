from django.conf import settings

# from django.utils import lru_cache, six
import functools
from django.urls import URLResolver, get_resolver

from .urlresolvers import SolidLocalePrefixPattern


def solid_i18n_patterns(*urls, prefix_default_language=True):
    """
    Modified copy of django i18n_patterns.
    Adds the language code prefix to every *non default language* URL pattern
    within this function. This may only be used in the root URLconf,
    not in an included URLconf.
    Do not adds any language code prefix to default language URL pattern.
    Default language must be set in settings.LANGUAGE_CODE
    """

    if not settings.USE_I18N:
        return list(urls)
    return [
        URLResolver(
            SolidLocalePrefixPattern(prefix_default_language=prefix_default_language),
            list(urls),
        )
    ]


@functools.lru_cache(maxsize=None)
def is_language_prefix_patterns_used(urlconf):
    """
    Returns `True` if the `SolidLocaleRegexURLResolver` is used
    at root level of the urlpatterns, else it returns `False`.
    """
    for url_pattern in get_resolver(urlconf).url_patterns:
        if isinstance(url_pattern.pattern, SolidLocalePrefixPattern):
            return True
    return False
