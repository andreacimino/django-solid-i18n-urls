# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import reverse
from django.urls import include, re_path as url
from django.utils import translation
from django.test.utils import override_settings
from django.views.generic import TemplateView
from solid_i18n.urls import solid_i18n_patterns

from .base import URLTestCaseBase


class PrefixDeprecationTestCase(URLTestCaseBase):

    def setUp(self):
        super(PrefixDeprecationTestCase, self).setUp()
        self.test_urls = [
            url(r'^$', TemplateView.as_view(template_name="test.html"), name='test'),
            url(r'^$', TemplateView.as_view(template_name="test2.html"), name='test2'),
        ]

    def test_with_and_without_prefix(self):
        """
        Ensure that solid_i18n_patterns works the same with or without a prefix.

        """
        self.assertEqual(
            solid_i18n_patterns(*self.test_urls)[0].regex,
            solid_i18n_patterns('', *self.test_urls)[0].regex,
        )


class TranslationReverseUrlTestCase(URLTestCaseBase):

    def _base_page_check(self, url_name, url_path):
        self.assertEqual(reverse(url_name), url_path)
        with translation.override('en'):
            self.assertEqual(reverse(url_name), url_path)
        with translation.override('ru'):
            self.assertEqual(reverse(url_name), '/ru' + url_path)

    # ----------- tests ----------

    def test_home_page(self):
        self._base_page_check('home', '/')

    def test_about_page(self):
        self._base_page_check('about', '/about/')

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_home_page_redirects(self):
        self._base_page_check('home', '/')

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_about_page_redirects(self):
        self._base_page_check('about', '/about/')


class TranslationAccessTestCase(URLTestCaseBase):
    PAGE_DATA = {
        "ru": {
            "home": 'Здравствуйте!',
            "about": 'Информация',
        },
        "en": {
            "home": 'Hello!',
            "about": 'Information',
        }
    }

    def _check_vary_accept_language(self, response):
        from django.conf import settings
        vary = response._headers.get('vary', ('', ''))[-1]
        if settings.SOLID_I18N_USE_REDIRECTS:
            req_path = response.request['PATH_INFO']
            if req_path.startswith('/en') or req_path.startswith('/ru'):
                self.assertFalse('Accept-Language' in vary)
            else:
                self.assertTrue('Accept-Language' in vary)
        else:
            self.assertFalse('Accept-Language' in vary)

    def _base_page_check(self, response, lang_code, page_code):
        self.assertEqual(response.status_code, 200)
        content = self.PAGE_DATA[lang_code][page_code]
        self.assertTrue(content in response.content.decode('utf8'))
        self.assertEqual(response.context['LANGUAGE_CODE'], lang_code)
        self._check_vary_accept_language(response)
        # content-language
        content_lang = response._headers.get('content-language', ('', ''))[-1]
        self.assertEqual(content_lang, lang_code)

    @property
    def en_http_headers(self):
        return dict(HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.8,ru;q=0.6')

    @property
    def ru_http_headers(self):
        return dict(HTTP_ACCEPT_LANGUAGE='ru-RU,ru;q=0.8,en;q=0.6')

    # ----------- tests ----------

    def test_home_page_en(self):
        with translation.override('en'):
            response = self.client.get(reverse('home'))
            self._base_page_check(response, "en", "home")

    def test_home_page_ru(self):
        with translation.override('ru'):
            response = self.client.get(reverse('home'))
            self._base_page_check(response, 'ru', "home")

    def test_about_page_en(self):
        with translation.override('en'):
            response = self.client.get(reverse('about'))
            self._base_page_check(response, "en", "about")

    def test_about_page_ru(self):
        with translation.override('ru'):
            response = self.client.get(reverse('about'))
            self._base_page_check(response, "ru", "about")

    def test_home_page_default_prefix_en_404(self):
        with translation.override('en'):
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 404)

    def test_home_page_default_prefix_ru_404(self):
        with translation.override('ru'):
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 404)

    # settings

    @override_settings(SOLID_I18N_PREFIX_STRICT=False)
    def test_about_page_strict_prefix_false(self):
        response = self.client.get('/my-slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'my')
        response = self.client.get('/ru/slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'ru')
        response = self.client.get('/pt-br/slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'pt-br')
        response = self.client.get('/pt-broughton/slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'pt-br')

    @override_settings(SOLID_I18N_PREFIX_STRICT=True)
    def test_about_page_strict_prefix_true(self):
        response = self.client.get('/my-slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'en')
        response = self.client.get('/ru/slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'ru')
        response = self.client.get('/pt-br/slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'pt-br')
        response = self.client.get('/pt-broughton/slug/')
        self.assertEqual(response._headers.get('content-language')[-1], 'en')

    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_about_page_default_prefix_en_with_prefix_first(self):
        # with prefix
        response = self.client.get('/en/about/')
        self._base_page_check(response, "en", "about")
        self.assertTrue('<test>/en/about/</test>' in str(response.content))
        # without prefix
        response = self.client.get('/about/')
        self._base_page_check(response, "en", "about")
        self.assertTrue('<test>/about/</test>' in str(response.content))
        # again with prefix
        response = self.client.get('/en/about/')
        self._base_page_check(response, "en", "about")
        self.assertTrue('<test>/en/about/</test>' in str(response.content))

    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_about_page_default_prefix_en_without_prefix_first(self):
        # without prefix
        response = self.client.get('/about/')
        self._base_page_check(response, "en", "about")
        self.assertTrue('<test>/about/</test>' in str(response.content))
        # with prefix
        response = self.client.get('/en/about/')
        self._base_page_check(response, "en", "about")
        self.assertTrue('<test>/en/about/</test>' in str(response.content))
        # again without prefix
        response = self.client.get('/about/')
        self._base_page_check(response, "en", "about")
        self.assertTrue('<test>/about/</test>' in str(response.content))

    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_about_page_default_prefix_ru(self):
        with translation.override('ru'):
            response = self.client.get('/en/about/')
            self._base_page_check(response, "en", "about")
            self.assertTrue('<test>/en/about/</test>' in str(response.content))

            response = self.client.get('/ru/about/')
            self._base_page_check(response, "ru", "about")
            self.assertTrue('<test>/ru/about/</test>' in response.content.decode('utf8'))

    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_home_page_default_prefix_en(self):
        """
        Check, that url with explicit default language prefix is still
        accessible.
        """
        with translation.override('en'):
            response = self.client.get('/en/')
            self._base_page_check(response, "en", "home")

    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_home_page_default_prefix_ru(self):
        """
        Check, that language is got from url prefix, even this laguage is
        not equal to client preferred langauge.
        """
        with translation.override('ru'):
            response = self.client.get('/en/')
            self._base_page_check(response, "en", "home")

    @override_settings(SOLID_I18N_DEFAULT_PREFIX_REDIRECT=True)
    def test_home_page_default_prefix_en_redirect(self):
        with translation.override('en'):
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 301)
            self.assertTrue('/en/' not in response['Location'])
            response = self.client.get(response['Location'])
            self._base_page_check(response, "en", "home")

    @override_settings(SOLID_I18N_DEFAULT_PREFIX_REDIRECT=True)
    def test_home_page_default_prefix_ru_redirect(self):
        with translation.override('ru'):
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 301)
            self.assertTrue('/en/' not in response['Location'])
            response = self.client.get(response['Location'])
            self._base_page_check(response, "en", "home")

    # use redirects

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_home_page_redirects_default_lang(self):
        response = self.client.get('/', **self.en_http_headers)
        self._base_page_check(response, "en", "home")

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_home_page_redirects_non_default_lang(self):
        response = self.client.get('/', **self.ru_http_headers)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/ru/' in response['Location'])
        response = self.client.get(response['Location'], **self.ru_http_headers)
        self._base_page_check(response, 'ru', "home")

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_about_page_redirects_default_lang(self):
        response = self.client.get('/about/', **self.en_http_headers)
        self._base_page_check(response, "en", "about")

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_about_page_redirects_non_default_lang(self):
        response = self.client.get('/about/', **self.ru_http_headers)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/ru/about/' in response['Location'])
        response = self.client.get(response['Location'], **self.ru_http_headers)
        self._base_page_check(response, "ru", "about")

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_home_page_prefix_default_prefix_en_404(self):
        response = self.client.get('/en/', **self.en_http_headers)
        self.assertEqual(response.status_code, 404)

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    def test_home_page_prefix_default_prefix_ru_404(self):
        response = self.client.get('/en/', **self.ru_http_headers)
        self.assertEqual(response.status_code, 404)

    # settings

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_set_language(self):
        response = self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/ru/')
        self.assertEqual(response.status_code, 200)

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_home_page_prefix_default_prefix_en(self):
        response = self.client.get('/en/', **self.en_http_headers)
        self._base_page_check(response, "en", "home")

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    @override_settings(SOLID_I18N_HANDLE_DEFAULT_PREFIX=True)
    def test_home_page_prefix_default_prefix_ru(self):
        response = self.client.get('/en/', **self.ru_http_headers)
        self._base_page_check(response, "en", "home")

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    @override_settings(SOLID_I18N_DEFAULT_PREFIX_REDIRECT=True)
    def test_home_page_prefix_default_prefix_en_redirect(self):
        response = self.client.get('/en/about/', **self.en_http_headers)
        self.assertEqual(response.status_code, 301)
        self.assertTrue('/about/' in response['Location'])
        self.assertFalse('/en/about/' in response['Location'])
        self.assertFalse('/ru/about/' in response['Location'])

    @override_settings(SOLID_I18N_USE_REDIRECTS=True)
    @override_settings(SOLID_I18N_DEFAULT_PREFIX_REDIRECT=True)
    def test_home_page_prefix_default_prefix_ru_redirect(self):
        response = self.client.get('/en/about/', **self.ru_http_headers)
        self.assertEqual(response.status_code, 301)
        self.assertTrue('/about/' in response['Location'])
        self.assertFalse('/en/about/' in response['Location'])
        self.assertFalse('/ru/about/' in response['Location'])
