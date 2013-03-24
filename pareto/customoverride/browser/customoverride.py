from zope.schema import Bytes
from zope.schema import ValidationError
from zope.interface import Interface
from zope.interface import implements
from zope.component import adapts
from zope.formlib import form
from zope.i18nmessageid import MessageFactory
from plone.app.controlpanel.form import ControlPanelForm

from OFS.Image import Image
from OFS.Image import getImageInfo
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName

_ = MessageFactory('CustomOverride')

LOGO_ID = 'logo.png'


class ImageValidationError(ValidationError):
    """Supplied file does not appear to be an image"""


def validateIsImage(value):
    ct, w, h = getImageInfo(value)
    if ct == '':
        raise ImageValidationError(value)
    return True


class ICustomOverrideSchema(Interface):

    image = Bytes(         
        title=_(u'New Image File'),
        description=_(u'Upload a new image file to replace the existing.'),
        required=True,
        constraint=validateIsImage)


class CustomOverrideAdapter(object):

    adapts(IPloneSiteRoot)
    implements(ICustomOverrideSchema)

    def __init__(self, context):
        self.context = context

    def get_image(self, image_id=LOGO_ID):
        image = ''
        try:
            image = self.context.restrictedTraverse(image_id)
        except KeyError:
            # there is no image.png that can be traversed to, punt
            pass

        return image

    def set_image(self, value):
        # it just seems better to do this in the 'on save' method below
        pass

    image = property(get_image, set_image)


class CustomOverride(ControlPanelForm):

    template = ViewPageTemplateFile('customoverride.pt')

    form_fields = form.FormFields(ICustomOverrideSchema)
    form_name = _(u'Image Upload Form')
    label = _(u'Custom override Control Panel')
    description = _(u'Override images in the design.')

    @property
    def current_image(self, image_id=LOGO_ID):
        tag = '<span class="discreet"><No Logo Found></span>'
        try:
            image = self.context.restrictedTraverse(image_id)
            tag = image.tag()
        except KeyError:
            # none was found, return the default tag
            pass

        return tag

    def _on_save(self, data=None):
        if data is None:
            # no form data, return without doing anything
            return

        new_image = data['image']
        if not new_image:
            # image not uploaded, return without doing anything
            return

        image_id = data['image_id']
        if not image_id:
            # image not uploaded, return without doing anything
            image_id = LOGO_ID

        skins = getToolByName(self.context, 'portal_skins')
        target = self.context
        if 'custom' in skins:
            target = skins['custom']

        if image_id in target:
            img = target[image_id]
            if isinstance(img, Image):
                # this is an OFS image, or subclass, we should have the
                # update_data method
                try:
                    img.update_data(new_image)
                    return
                except TypeError, e:
                    # there is a problem with the image data, it's unicode
                    raise e
                except AttributeError, e:
                    # no update_data method.  make a new one and replace this
                    # one
                    pass
            else:
                # let's override it, it isn't an expected type.
                pass

        img = Image(image_id, 'Custom Site Logo', new_image)
        target._setObject(image_id, img)
        return
