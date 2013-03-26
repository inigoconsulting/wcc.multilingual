from wcc.common.interfaces import ILanguageDependentFieldsManager

def set_default_translation(event):
    origin = event.object
    target = event.target
    ILanguageDependentFieldsManager(origin).copy_fields(target)
    target.reindexObject()
