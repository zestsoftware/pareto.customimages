from zope.schema import Bytes
from zope.schema import ValidationError
from zope.interface import Interface
from zope.interface import implements
from zope.component import adapts
from zope.formlib import form
from zope.event import notify
from zope.i18nmessageid import MessageFactory
from plone.app.controlpanel.form import ControlPanelForm
from plone.protect import CheckAuthenticator
from plone.app.controlpanel.events import ConfigurationChangedEvent

from plone.app.form.validators import null_validator

from OFS.Image import Image
from OFS.Image import getImageInfo

from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName

_ = MessageFactory('pareto.customimages')

LOGO_ID = 'logo.png'
INTERFACE = 'pareto.customimages.browser.customimages.ICustomImagesSchema'

class ImageValidationError(ValidationError):
    """Supplied file does not appear to be an image"""


def validateIsImage(value):
    ct, w, h = getImageInfo(value)
    if ct == '':
        raise ImageValidationError(value)
    return True


class ICustomImagesSchema(Interface):

    image = Bytes(         
        title=_(u'New Image File'),
        description=_(u'Upload a new image file to replace the existing.'),
        required=True,
        constraint=validateIsImage)


class CustomImagesAdapter(object):

    adapts(IPloneSiteRoot)
    implements(ICustomImagesSchema)

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


class CustomImages(ControlPanelForm):

    template = ViewPageTemplateFile('customimages.pt')

    form_fields = form.FormFields(ICustomImagesSchema)
    form_name = _(u'Upload Form')
    label = _(u'Custom Images Control Panel')
    description = _(u'Override images in the design.')

    @form.action(_(u'label_save', default=u'Save'), name=u'save')
    def handle_edit_action(self, action, data):
        CheckAuthenticator(self.request)
        if form.applyChanges(self.context, self.form_fields, data,
                             self.adapters):
            self.status = _("Changes saved.")
            notify(ConfigurationChangedEvent(self, data))
            self._on_save(data)
        else:
            self.status = _("No changes made.")

    @form.action(_(u'label_cancel', default=u'Cancel'),
                 validator=null_validator,
                 name=u'cancel')
    def handle_cancel_action(self, action, data):
        IStatusMessage(self.request).addStatusMessage(_("Changes canceled."),
                                                      type="info")
        url = getMultiAdapter((self.context, self.request),
                              name='absolute_url')()
        self.request.response.redirect(url + '/plone_control_panel')
        return ''

    @form.action(_(u'label_clear', default=u'Clear'), 
                 validator=null_validator,
                 name=u'clear')
    def handle_clear_action(self, action, data):
        skins = getToolByName(self.context, 'portal_skins')
        target = skins.get('custom', self.context)
        image_id = self.request.form.get('image_id', None)
        if not image_id:
            self.status = _("No image id.")
        elif image_id in target:
            target._delObject(image_id)
            self.status = _("Changes saved.")
        else:
            self.status = _("No changes made.")

    def images(self):
        registry = getUtility(IRegistry)
        value = registry.records.get('%s.images' % INTERFACE).value
        images = dict([tuple([str(w) if i == 0 else w 
                              for i, w in enumerate(v.split('|'))]) 
                       for v in value])
        return images

    def current_image(self, image_id=LOGO_ID):
        tag = '<span class="discreet"><No Logo Found></span>'
        try:
            image = self.context.restrictedTraverse(image_id)
            tag = image.tag(style='height: auto; max-width: 100%; '
                                  'border: 1px dashed #999;')
        except KeyError:
            # none was found, return the default tag
            pass

        return tag
    
    def _on_save(self, data=None):
        if data is None:
            # no form data, return without doing anything
            return

        new_image = data.get('image', None)
        if not new_image:
            # image not uploaded, return without doing anything
            return

        image_id = self.request.form.get('image_id', None)
        if image_id:
            image_id = str(image_id)
        else:
            image_id = LOGO_ID

        image_title = self.request.form.get('image_title', None)
        if not image_title:
            image_title = u'Custom Logo'

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

        img = Image(image_id, 'Custom %s' % image_title, new_image)
        target._setObject(image_id, img)
        return
