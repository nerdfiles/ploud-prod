""" validators """
from ptah import form
from ploud.frontend.models import Session, User, Site
from ploud.frontend.config import PLOUD, ALLOWED_SITE_NAME_CHARS


def checkEmail(node, email):
    if Session.query(User).filter_by(email=email).first() is not None:
        raise form.Invalid(node, 'E-Mail address aready is in use.')

    
def checkSitename(node, site_name):
    site_name_set = set(site_name)
    if not site_name_set.issubset(ALLOWED_SITE_NAME_CHARS):
        raise form.Invalid(
            node, "We couldn't create your Plone site. You've typed invalid characters in site name.  Please only use lowercase alpha-numeric characters, the hyphen, and the underscore.")
    elif site_name in PLOUD.reserved_sitenames:
        raise form.Invalid(
            node, "We couldn't create your Plone site. You've chosen a reserved site name.  Please try a different site name.")
    else:
        exists = Session.query(Site).filter_by(site_name=site_name).first()
        if exists is not None:
            raise form.Invalid(
                node, "We couldn't create your Plone site. Site with this name already exists. Please try a different site name.")
