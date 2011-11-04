""" signup form """
import datetime, random
import simplejson as json
from email.mime.text import MIMEText
import colander
import transaction
from pyramid.httpexceptions import HTTPFound
from pyramid import renderers
from pyramid.security import remember, authenticated_userid

from ptah import view, config, form

from ploud.utils import ploud_config
from ploud.utils.policy import POLICIES
from ploud.frontend import utils, validators
from ploud.frontend.config import log, PLOUD, ALLOWED_SITE_NAME_CHARS
from ploud.frontend.models import Session, User, Site
from root import PloudApplicationRoot


def lower(s):
    if isinstance(s, basestring):
        return s.lower()
    return s

view.register_route('frontend-signup-validate', '/signup/validate')
view.register_route('frontend-validate', '/validate')


SignupSchema = form.Fieldset(
    form.TextField(
        'signup-email',
        preparer = lower,
        validator = form.All(form.Email(), validators.checkEmail)),

    form.TextField(
        'signup-site-name',
        preparer = lower,
        validator = validators.checkSitename),
    )


@view.pview(route='frontend-signup-validate')
def validate_signup_view(request):
    errors, data = validate_signup(request)

    response = request.response
    response.content_type = 'text/json'
    response.body = json.dumps(errors)
    return response


def validate_signup(request):
    fields = SignupSchema.bind(None, request.POST)
    data, errs = fields.extract()

    errors = {}
    for err in errs:
        if err.field:
            errors[err.field.name] = err.msg

    if not errors:
        toc = request.POST.get('signup-accept-toc', '').lower()
        if toc not in ('true', '1'):
            errors = {'signup-accept-toc': 
                      'You must accept Terms and Conditions'}

    return errors, data


class SignupView(view.View):
    view.pview('signup', PloudApplicationRoot)
    
    content_type = 'text/json'

    def update(self):
        allowed = PLOUD.registration
        if not allowed:
            raise HTTPFound(location = '/waitinglist.html')

        principal = authenticated_userid(self.request)
        if principal:
            raise HTTPFound(location = '/dashboard.html')

        errors, data = validate_signup(self.request)
        if errors:
            return

        email = data['signup-email']
        site_name = data['signup-site-name']
        password = ''.join(
            random.choice(ALLOWED_SITE_NAME_CHARS) for i in range(8))

        user = User(email, password, 98)
        token = user.token
        Session.add(user)
        Session.flush()

        uri = user.uri

        send_activation(email, token)

        try:
            utils.provision_site(user, 'plone41', site_name)
        except Exception, exc:
            transaction.abort()
            self.errors = {'signup-site-name': str(exc)}
            log.exception('Site provision problem')
            return

        headers = remember(self.request, uri)
        raise HTTPFound(location='/dashboard.html', headers=headers)

    def render(self):
        raise HTTPFound(location='/index.html')


class Validate(view.View):
    view.pview(route='frontend-validate')

    def update(self):
        token = self.request.GET.get('token')

        user = Session.query(User).filter_by(token=token).first()
        if user is not None:
            user.type = 0
            user.token = None
            user.validated = datetime.datetime.now()

            # change policy to 0 (free)
            conn = ploud_config.PLOUD_POOL.getconn()
            cursor = conn.cursor()
            POLICIES[user.type].apply(user.id, cursor)
            cursor.close()
            conn.commit()
            ploud_config.PLOUD_POOL.putconn(conn)

            headers = remember(self.request, user.uri)
            raise HTTPFound(location = '/change-password.html', headers = headers)
        else:
            raise HTTPFound(location="/index.html?message=Can't validate email address.")


def send_activation(email, token):
    mail_template = renderers.get_renderer(
        'newui/validate_email.txt').implementation()

    data = dict(host=PLOUD.host, email=email, token=token)
    msg = MIMEText(str(mail_template(**data)))
    msg['Subject'] = 'Activate Your Ploud Account'
    msg['From'] = PLOUD.email_from
    msg['To'] = email

    config.Settings['mail'].Mailer.send(PLOUD.email_from, email, msg)
