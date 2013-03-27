from wcc.common.interfaces import ILanguageDependentFieldsManager
from zope import interface
from zope.component import getUtility

from plone.dexterity import utils
from plone.dexterity.interfaces import IDexterityFTI

from plone.multilingual.interfaces import ILanguageIndependentFieldsManager

from plone.multilingualbehavior.interfaces import ILanguageIndependentField
from z3c.relationfield.interfaces import IRelationValue

from plone.multilingual.interfaces import ILanguage
from zope.component import queryAdapter
from plone.multilingual.interfaces import ITranslationManager

from zope.app.intid.interfaces import IIntIds
from zope import component
from z3c.relationfield import RelationValue
from archetypes.multilingual.interfaces import IArchetypesTranslatable
from plone.multilingualbehavior.interfaces import IDexterityTranslatable
from five import grok

_marker = []

EXCLUDES=['language', 'creators', 'id', 'rights', 'contributors']

class DexterityLanguageDependentFieldsManager(grok.Adapter):
    grok.context(IDexterityTranslatable)
    interface.implements(ILanguageDependentFieldsManager)
    
    def __init__(self, context):
        self.context = context

    def copy_fields(self, translation):
        fti = getUtility(IDexterityFTI, name=self.context.portal_type)
        schemas = []
        schemas.append(fti.lookupSchema())

        for behavior_schema in \
                utils.getAdditionalSchemata(self.context, self.context.portal_type):
            if behavior_schema is not None:
                schemas.append(behavior_schema)

        for schema in schemas:
            for field_name in schema:
                if field_name in EXCLUDES:
                    continue
                if not ILanguageIndependentField.providedBy(schema[field_name]):
                    value = getattr(schema(self.context), field_name, _marker)
                    if IRelationValue.providedBy(value):
                        obj = value.to_object
                        adapter = queryAdapter(translation, ILanguage)
                        trans_obj = ITranslationManager(obj).get_translation(adapter.get_language())
                        if trans_obj:
                            intids = component.getUtility(IIntIds)
                            value = RelationValue(intids.getId(trans_obj))
                    if not (value == _marker):
                        # We check if not (value == _marker) because z3c.relationfield has an __eq__
                        setattr(schema(translation), field_name, value)


class ArchetypesLanguageDependentFieldsManager(grok.Adapter):
    grok.context(IArchetypesTranslatable)
    interface.implements(ILanguageDependentFieldsManager)

    def __init__(self, context):
        self.context = context

    def _copy_field(self, field, translation):
        accessor = field.getEditAccessor(self.context)
        if not accessor:
            accessor = field.getAccessor(self.context)
        if accessor:
            data = accessor()
        else:
            data = field.get(self.context)
        mutator = field.getMutator(translation)
        if mutator is not None:
            # Protect against weird fields, like computed fields
            mutator(data)
        else:
            field.set(translation, data)

    def copy_fields(self, translation):
        dest_schema = translation.Schema()
        schema = self.context.Schema()
        fields = schema.filterFields(languageIndependent=False)
        fields_to_copy = [x for x in fields if x.getName() in dest_schema]
        fields_to_copy = [x for x in fields if x.getName() not in EXCLUDES]
        for field in fields_to_copy:
            self._copy_field(field, translation)
    
