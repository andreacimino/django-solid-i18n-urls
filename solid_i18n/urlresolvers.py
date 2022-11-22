import re
from django.utils.translation import get_language
from django.urls import clear_url_caches
from django.conf import settings
from .memory import get_language_from_path
from django.urls import LocalePrefixPattern

# from django.urls import (
#         NoReverseMatch, URLPattern as RegexURLPattern, URLResolver as RegexURLResolver, ResolverMatch, Resolver404, get_script_prefix, reverse, reverse_lazy, resolve
# )


class SolidLocalePrefixPattern(LocalePrefixPattern):
    """
    A URL resolver that always matches the active language code as URL prefix,
    but for default language non prefix is used.

    Rather than taking a regex argument, we just override the ``regex``
    function to always return the active language-code as regex.
    """

    def __init__(self, prefix_default_language, *args, **kwargs):
        super(SolidLocalePrefixPattern, self).__init__(False, *args, **kwargs)
        self.compiled_with_default = False
        self._regex_dict = {}

    # @property
    # def regex(self):
    #     # This is only used by reverse() and cached in _reverse_dict.
    #     return re.compile(re.escape(self.language_prefix))

    @property
    def language_prefix(self):
        language_code = get_language() or settings.LANGUAGE_CODE
        # if language_code == settings.LANGUAGE_CODE and not self.prefix_default_language:
        #    return ""
        # else:
        return "%s/" % language_code

    def match(self, path):
        language_code = get_language() or settings.LANGUAGE_CODE
        language_prefix = self.language_prefix

        if language_code == settings.LANGUAGE_CODE and not self.prefix_default_language:
            if path == language_code + "/":
                if not settings.SOLID_I18N_HANDLE_DEFAULT_PREFIX:
                    return None
        #            import pdb

        #           pdb.set_trace()
        #     if path.startswith(language_prefix):
        #         import pdb

        #         pdb.set_trace()
        #         return None

        language_prefix = self.language_prefix
        if path.startswith(language_prefix):
            return path[len(language_prefix) :], (), {}

        return path[0:], (), {}

    #  return None

    @property
    def regex(self):
        """
        For non-default language always returns regex with langauge prefix.
        For default language returns either '', eigher '^{lang_code}/',
        depending on SOLID_I18N_HANDLE_DEFAULT_PREFIX and request url.

        If SOLID_I18N_HANDLE_DEFAULT_PREFIX == True and default langauge
        prefix is present in url, all other urls will be reversed with default
        prefix.
        Otherwise, all other urls will be reversed without default langauge
        prefix.
        """
        #  import pdb

        #  pdb.set_trace()
        #
        language_code = get_language()
        handle_default_prefix = getattr(
            settings, "SOLID_I18N_HANDLE_DEFAULT_PREFIX", False
        )
        if language_code not in self._regex_dict:
            if language_code != settings.LANGUAGE_CODE:
                regex = "^%s/" % language_code
            elif handle_default_prefix:
                if get_language_from_path() == settings.LANGUAGE_CODE:
                    self.compiled_with_default = True
                    regex = "^%s/" % language_code
                else:
                    self.compiled_with_default = False
                    regex = ""
            else:
                regex = ""
            self._regex_dict[language_code] = re.compile(regex, re.UNICODE)
        elif handle_default_prefix and language_code == settings.LANGUAGE_CODE:
            language_from_path = get_language_from_path()
            regex = None
            if self.compiled_with_default and not language_from_path:
                # default language is compiled with prefix, but now client
                # requests the url without prefix. So compile other urls
                # without prefix.
                regex = ""
                self.compiled_with_default = False
            elif (
                not self.compiled_with_default
                and language_from_path == settings.LANGUAGE_CODE
            ):
                # default language is compiled without prefix, but now client
                # requests the url with prefix. So compile other urls
                # with prefix.
                regex = "^%s/" % language_code
                self.compiled_with_default = True
            if regex is not None:
                clear_url_caches()
                self._regex_dict[language_code] = re.compile(regex, re.UNICODE)
        return self._regex_dict[language_code]
