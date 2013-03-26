from collective.grok import gs
from wcc.multilingual import MessageFactory as _

@gs.importstep(
    name=u'wcc.multilingual', 
    title=_('wcc.multilingual import handler'),
    description=_(''))
def setupVarious(context):
    if context.readDataFile('wcc.multilingual.marker.txt') is None:
        return
    portal = context.getSite()

    # do anything here
