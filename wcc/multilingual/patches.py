import logging
logger = logging.getLogger('wcc.multilingual')

def _patch_canonicals_cleanup():
    # this cleanup the value of canonicals, so that we dont left with None
    # dangling around

    from plone.multilingual.storage import CanonicalStorage
    from plone.app.uuid.utils import uuidToObject

    if getattr(CanonicalStorage, '__wcc_canonical_cleanup_patch', False):
        return
    logger.info('Patching with canonical cleanup patch')

    _orig_get_canonicals = CanonicalStorage.get_canonicals
    def get_canonicals(self):
        canonicals = _orig_get_canonicals(self)
        for c in canonicals:
            obj = uuidToObject(c)
            if obj is None:
                self.remove_canonical(c)
        return _orig_get_canonicals(self)
    CanonicalStorage.get_canonicals = get_canonicals
    CanonicalStorage.__wcc_canonical_cleanup_patch = True

_patch_canonicals_cleanup()

def _patch_remove_nontranslated_selector():
    # this patch remove the languages from the selector if there are no
    # translated contents for it

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

_marker = []
def _patch_dexterity_languageindependentrelationlist():
    # XXX: FIXME:
    # This should be going upstream
    # - add multilingual support for RelationList
    from plone.multilingualbehavior.utils import LanguageIndependentFieldsManager

    if getattr(LanguageIndependentFieldsManager, '__inigo_relationlist_patched', False):
        return 

    from plone.dexterity.interfaces import IDexterityFTI
    from z3c.relationfield.interfaces import IRelationValue, IRelationList
    from z3c.relationfield import RelationValue
    from plone.multilingual.interfaces import ITranslationManager
    from plone.dexterity import utils
    from plone.multilingualbehavior.interfaces import ILanguageIndependentField
    from zope.component import queryAdapter
    from plone.multilingual.interfaces import ILanguage
    from zope import component
    from zope.app.intid.interfaces import IIntIds

    def _translate_relation_values(self, translation, values):
        result = []
        for v in values:
            obj = v.to_object
            adapter = queryAdapter(translation, ILanguage)
            trans_obj = ITranslationManager(obj).get_translation(adapter.get_language())
            if trans_obj:
                intids = component.getUtility(IIntIds)
                val = RelationValue(intids.getId(trans_obj))
                result.append(val)
            else:
                result.append(v)
        return result

    _orig_copy_fields = LanguageIndependentFieldsManager.copy_fields
    def copy_fields(self, translation):
        _orig_copy_fields(self, translation)

        fti = component.getUtility(IDexterityFTI, name=self.context.portal_type)
        schemas = []
        schemas.append(fti.lookupSchema())

        for behavior_schema in \
                utils.getAdditionalSchemata(self.context, self.context.portal_type):
            if behavior_schema is not None:
                schemas.append(behavior_schema)

        for schema in schemas:
            for field_name in schema:
                if (ILanguageIndependentField.providedBy(schema[field_name]) and
                    IRelationList.providedBy(schema[field_name])):
                    value = getattr(schema(self.context), field_name, _marker)
                    if value:
                        value = _translate_relation_values(self, translation, value)
                    if not (value == _marker):
                        # We check if not (value == _marker) because z3c.relationfield has an __eq__
                        setattr(schema(translation), field_name, value)

    LanguageIndependentFieldsManager.copy_fields = copy_fields
    LanguageIndependentFieldsManager.__inigo_relationlist_patched = True

_patch_dexterity_languageindependentrelationlist()

def _patch_archetypes_languageindependentreferencefield():
     # XXX: FIXME:
    # This should be going upstream
    # - add multilingual support for ReferenceField

    from archetypes.multilingual.utils import LanguageIndependentFieldsManager

    if getattr(LanguageIndependentFieldsManager, '__inigo_relationlist_patched', False):
        return

    from Products.Archetypes.interfaces import IReferenceField
    from plone.multilingual.interfaces import ITranslationManager
    from zope.component import queryAdapter
    from plone.multilingual.interfaces import ILanguage
    from Products.Archetypes.interfaces.referenceable import IReferenceable

    def _translate_reference_value(self, translation, uid):
        if not uid:
            return uid

        brains = self.context.portal_catalog(UID=uid, Language='all')
        if not brains:
            return uid

        obj = brains[0].getObject()
        adapter = queryAdapter(translation, ILanguage)
        trans_obj = ITranslationManager(obj).get_translation(adapter.get_language())
        if trans_obj:
            return IReferenceable(trans_obj).UID()
        return uid

    def _translate_multireference_values(self, translation, uids):
        if not uids:
            return uids

        result = []
        for uid in uids:
            newuid = _translate_reference_value(self, translation, uid)
            result.append(newuid)

        return result

    _orig_copy_field = LanguageIndependentFieldsManager._copy_field

    def _copy_field(self, field, translation):
        if not IReferenceField.providedBy(field):
            return _orig_copy_field(self, field, translation)

        accessor = field.getEditAccessor(self.context)
        if not accessor:
            accessor = field.getAccessor(self.context)
        if accessor:
            data = accessor()
        else:
            data = field.get(self.context)

        if getattr(field, 'multiValued', False):
            data = _translate_multireference_values(self, translation, data)
        else:
            data = _translate_reference_value(self, translation, data)

        mutator = field.getMutator(translation)
        if mutator is not None:
            # Protect against weird fields, like computed fields
            mutator(data)
        else:
            field.set(translation, data)

    LanguageIndependentFieldsManager._copy_field = _copy_field
    LanguageIndependentFieldsManager.__inigo_relationlist_patched = True

_patch_archetypes_languageindependentreferencefield()
