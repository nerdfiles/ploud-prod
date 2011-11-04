import ptah
import sqlahelper as psa
import sqlalchemy as sqla
from zope import interface
from models import Session, User


class PloudProvider(object):

    def authenticate(self, creds):
        login, password = creds['login'], creds['password']

        user = User.get(login)

        if user is not None:
            if ptah.passwordTool.check(user.password,password):
                return user

    def get_principal(self, uri):
        return User.getByURI(uri)

    def get_principal_bylogin(self, login):
        return User.get(login)

    _sql_search = ptah.QueryFreezer(
        lambda: Session.query(User) \
        .filter(User.email.contains(sqla.sql.bindparam('term')))
        .order_by(sqla.sql.asc('email')))

    def search(self, term):
        for user in self._sql_search.all(term = '%%%s%%'%term):
            yield user


provider = PloudProvider()
ptah.register_uri_resolver('user-ploud', provider.get_principal)
ptah.register_auth_provider('ploud', provider)
ptah.register_principal_searcher('ploud', provider.search)
