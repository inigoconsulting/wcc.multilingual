
def _patch_remove_nontranslated_selector():
    from plone.app.multilingual.browser.selector import LanguageSelectorViewlet
    from plone.app.multilingual.browser.selector import NOT_TRANSLATED_YET_TEMPLATE
    if getattr(LanguageSelectorViewlet, '__inigo_patched_languageselector',
            False):
        return

    _orig_languages = LanguageSelectorViewlet.languages
    def languages(self):
        langs = _orig_languages(self)
        return [
            i for i in langs if NOT_TRANSLATED_YET_TEMPLATE not in i['url']
        ]

    LanguageSelectorViewlet.languages = languages
    LanguageSelectorViewlet.__inigo_patched_languageselector = True

_patch_remove_nontranslated_selector()
