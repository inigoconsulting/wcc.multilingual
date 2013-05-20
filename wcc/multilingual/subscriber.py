from wcc.common.interfaces import ILanguageDependentFieldsManager
from DateTime import DateTime
from wcc.multilingual.interfaces import ITranslationDateEnabled

def set_default_translation(event):
    origin = event.object
    target = event.target
    ILanguageDependentFieldsManager(origin).copy_fields(target)
    if ITranslationDateEnabled.providedBy(target):
        target.translation_date = DateTime()
    target.reindexObject()
