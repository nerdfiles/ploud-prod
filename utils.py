""" utils """
import transaction
from datetime import datetime
from ploud.utils import ploud_config
from ploud.utils.policy import POLICIES
from ploud.utils.disable import disableVhosts, enableVhosts
from ploud.utils.vhost import addVirtualHosts, removeVirtualHosts

from ploud.frontend import models, tmpl
from ploud.frontend.config import PLOUD


def disableHost(site):
    names = [str(host.host)
             for host in
                models.Session.query(models.Host).filter_by(id=site.id)]
    site.disabled = True

    # we have to commit site changes because
    # next call update file on filesystem and we won't able
    # to rollback change
    #transaction.commit()
    disableVhosts(names)


def enableHost(site):
    names = [str(host.host)
             for host in
                models.Session.query(models.Host).filter_by(id=site.id)]
    site.disabled = False

    # we have to commit site changes because
    # next call update file on filesystem and we won't able
    # to rollback change
    #transaction.commit()
    enableVhosts(names)


rfc822_specials = '()<>@,;:\\"[]'

def isValidMailAddress(addr):
    """Returns True if the email address is valid and False if not."""
    # First we validate the name portion (name@domain)
    c = 0
    while c < len(addr):
        if addr[c] == '@':
            break
        # Make sure there are only ASCII characters
        if ord(addr[c]) <= 32 or ord(addr[c]) >= 127:
            return False
        # A RFC-822 address cannot contain certain ASCII characters
        if addr[c] in rfc822_specials:
            return False
        c = c + 1

    # check whether we have any input and that the name did not end with a dot
    if not c or addr[c - 1] == '.':
        return False

    # check also starting and ending dots in (name@domain)
    if addr.startswith('.') or addr.endswith('.'):
        return False

    # Next we validate the domain portion (name@domain)
    domain = c = c + 1
    # Ensure that the domain is not empty (name@)
    if domain >= len(addr):
        return False
    count = 0
    while c < len(addr):
        # Make sure that domain does not end with a dot or has two dots in a row
        if addr[c] == '.':
            if c == domain or addr[c - 1] == '.':
                return False
            count = count + 1
        # Make sure there are only ASCII characters
        if ord(addr[c]) <= 32 or ord(addr[c]) >= 127:
            return False
        # A RFC-822 address cannot contain certain ASCII characters
        if addr[c] in rfc822_specials:
            return False
        c = c + 1
    if count >= 1:
        return True
    else:
        return False


def provision_site(user, site_type, site_name, template_id=''):
    # create site entry
    site = models.Site(user.id, site_type, site_name)
    site.last_accessed = datetime.now()
    models.Session.add(site)
    models.Session.flush()

    # create host
    hostname = '%s.%s'%(site_name, PLOUD.domain)
    host = models.Host(site.id, hostname.lower())
    models.Session.add(host)
    addVirtualHosts((str(hostname),), 'plone41')
    POLICIES[user.type].changeHostsPolicy((hostname,), site_name)

    # Create the database.
    conn = ploud_config.CLIENTS_POOL.getconn()
    try:
        tmpl.create_site(conn, site.id, template_id=template_id, type=site_type)
    except NameError:
        tmpl.create_site(conn, site.id, type=site_type)
    conn.commit()
    ploud_config.CLIENTS_POOL.putconn(conn)
    transaction.commit()

    # change owner of new site
    if PLOUD.maintence is not None:
        PLOUD.maintence.execute(hostname, 'ploud-fix-owner')

    return site
