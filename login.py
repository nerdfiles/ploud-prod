""" login """
import simplejson as json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from sqlalchemy.sql import expression as expr

from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid, remember, forget

from ptah import view, config
from ptah.token import service as tokenService

from ploud.frontend.models import Session, User
from ploud.frontend.config import log, PLOUD, PASSWORD_RESET_TOKEN_TYPE


view.register_route('frontend-login', '/login.html')
view.register_route('frontend-login-validate', '/login.html/validate')
view.register_route('frontend-logout', '/logout.html')
view.register_route('frontend-resetpw', '/reset-password.html')
view.register_route('frontend-resetpw-v','/reset-password.html/validate')
view.register_route('frontend-changepw', '/change-password.html')


@view.pview(route='frontend-login-validate')
def validate_login_view(request):
    errors = validate_login(request)

    response = request.response
    response.content_type = 'text/json'
    response.body = json.dumps(errors)
    return response


def validate_login(request):
    errors = {}

    email = request.POST.get('login-email', '').lower()
    password = request.POST.get('login-password', '')

    user = Session.query(User).filter_by(email=email).first()
    if user is None:
        errors['login-email'] = 'Account not found.'
        return errors

    if user.password != password:
        errors['login-password'] = 'Incorrect password, please try again.'

    return errors


class LoginView(view.View):
    view.pview(route='frontend-login')

    status = ''
 
    def render(self):
        request = self.request
        principal = authenticated_userid(request)
        if principal:
            raise HTTPFound(location='/dashboard.html')

        errors = validate_login(request)
        if errors:
            self.status = errors
            raise HTTPFound(location='/index.html')

        email = request.POST.get('login-email', '').lower()
        user = Session.query(User).filter_by(email=email).first()
        
        headers = remember(request, user.uri)
        raise HTTPFound(location='/dashboard.html', headers=headers)


class LogoutView(view.View):
    view.pview(route='frontend-logout')

    def render(self):
        request = self.request

        principal = authenticated_userid(request)
        if principal is not None:
            headers = forget(request)
            raise HTTPFound(location='/index.html', headers=headers)
        else:
            raise HTTPFound(location='/index.html')


@view.pview(route='frontend-resetpw-v')
def validate_resetpw_view(request):
    errors = validate_resetpw(request)

    response = request.response
    response.content_type = 'text/json'
    response.body = json.dumps(errors)
    return response


def validate_resetpw(request):
    email = request.POST.get('login-email', '').lower()

    if not email:
        return {'login-email': u"Can't find login information."}

    user = Session.query(User).filter_by(email=email).first()
    if user is None:
        return {'login-email': u"Can't find login information."}

    return {}


class ResetPassword(view.View):
    view.pview(route='frontend-resetpw', layout='page',
                     template = view.template('newui/resetpassword.pt'))

    status = None

    def update(self):
        if "form.resetpw" not in self.request.POST:
            return

        errors = validate_resetpw(self.request)

        if not errors:
            token = tokenService.generate(
                PASSWORD_RESET_TOKEN_TYPE, self.user.id)
            send_new_password_email(self.email, token)
            success = "You've reset your password. Please check your email."
            raise HTTPFound(location='/index.html?message=%s'%success)


class ChangePassword(view.View):
    view.pview(route='frontend-changepw', layout='page',
                     template = view.template('newui/changepassword.pt'))

    message = ''
    token = None
    userid = None

    td = timedelta(hours=1)

    def update(self):
        request = self.request

        principal = authenticated_userid(request)
        user = User.getByURI(principal)
        if user is None:
            self.token = token = request.params.get('token')
            if token:
                self.userid = tokenService.get(token)
                if self.userid is None:
                    raise HTTPFound(location='/reset-password.html')

                user = User.getById(self.userid)

        if user is None:
            raise HTTPFound(location='/reset-password.html')

        if 'form-change' in request.POST:
            password = request.POST.get('change-password')
            confirm = request.POST.get('confirm-password')
            if not password:
                return

            if password != confirm:
                self.message = \
                    'Password and Confirm password has to be identical.'

            if self.userid is not None:
                tokenService.remove(self.token)

            user.password = password
            user.validated = True

            headers = {}
            if not principal:
                headers = remember(request, user.uri)

            raise HTTPFound(
                location='/dashboard.html?message=Password has been changed.',
                headers = headers)

        token = request.params.get('token')
        if not token and user is None:
            raise HTTPFound(location='/dashboard.html')


mail_template = view.template('newui/reset_password.txt')

def send_new_password_email(email, token):
    data = dict(host=PLOUD.host, email=email, token=token)
    msg = MIMEText(str(mail_template(**data)))
    msg['Subject'] = "You've Reset Your Ploud Password"
    msg['From'] = PLOUD.email_from
    msg['To'] = email

    config.Settings['mail'].Mailer.send(PLOUD.email_from, email, msg)
