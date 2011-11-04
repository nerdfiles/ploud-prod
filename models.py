""" models """
import datetime
import uuid, transaction
import sqlahelper as psa
import sqlalchemy as sqla
from zope import interface

import ptah
from ptah import config
from ploud.frontend.config import log

Base = psa.get_base()
Session = psa.get_session()


class User(Base):

    __tablename__ = 'users'

    id = sqla.Column(sqla.Integer, sqla.Sequence('users_seq'), primary_key=True)
    email = sqla.Column(sqla.Unicode(255), unique=True)
    password = sqla.Column(sqla.Unicode(255))
    join_date = sqla.Column(sqla.DateTime)
    validated = sqla.Column(sqla.DateTime)
    token = sqla.Column(sqla.Unicode(255))
    type = sqla.Column(sqla.Integer, default=0)
    removes = sqla.Column(sqla.Integer, default=0)
    transfers = sqla.Column(sqla.Integer, default=0)

    sites = sqla.orm.relationship('Site', backref='user')

    def __init__(self, email, password, type=0):
        super(Base, self).__init__()

        self.email = email
        self.password = password
        self.join_date = datetime.datetime.now()
        self.validated = None # until Date entry was validated
        self.token = str(uuid.uuid4())
        self.type = type
        self.removes = 0
        self.transfers = 0

    @property
    def uri(self):
        return 'user-ploud:%s'%self.id

    @property
    def name(self):
        return self.email

    @property
    def login(self):
        return self.email

    @classmethod
    def get(self, email):
        return Session.query(User).filter_by(email=email).first()

    @classmethod
    def getById(self, id):
        return Session.query(User).filter_by(id=id).first()

    @classmethod
    def getByURI(cls, uri):
        if uri and uri.startswith('user-ploud'):
            try:
                id = int(uri[11:])
                return cls.getById(id)
            except:
                pass

    def membership_label(self):
        policy_labels = {0 : 'Member',
                         1 : 'Basic Member',
                         2 : 'Full Member',
                        98 : 'Pending Member',
                        99 : 'Administrator'}
        return policy_labels[self.type]

    def __str__(self):
        return self.email


class Site(Base):

    __tablename__ = 'sites'

    id = sqla.Column(sqla.Integer, sqla.Sequence('sites_seq'), primary_key=True)
    site_name = sqla.Column(sqla.Unicode(255))
    typeof = sqla.Column(sqla.Unicode(255))
    user_id = sqla.Column(sqla.Integer, sqla.ForeignKey('users.id'))
    size = sqla.Column(sqla.Integer, default=0)
    bwin = sqla.Column(sqla.Integer, default=0)
    bwout = sqla.Column(sqla.Integer, default=0)
    disabled = sqla.Column(sqla.Boolean, default=False)
    removed = sqla.Column(sqla.Boolean, default=False)
    last_accessed = sqla.Column(sqla.DateTime)
    packed = sqla.Column(sqla.DateTime)
    packed_size = sqla.Column(sqla.Integer, default=0)

    User = sqla.orm.relation('User')
    hosts = sqla.orm.relationship('Host', backref='sites')

    def __init__(self, user_id, typeof, site_name):
        super(Base, self).__init__()

        self.site_name = site_name
        self.typeof = typeof
        self.user_id = user_id

    def set_owner(self, email):
        user = Session.query(User).filter_by(email=email).first()
        self.user_id = user.id


class Host(Base):
    """ Hostname for a site """
    __tablename__ = 'vhost'

    id = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('sites.id',
                        onupdate='CASCADE', ondelete='CASCADE'))
    host = sqla.Column(sqla.Unicode(255), primary_key=True)

    def __init__(self, id, host):
        super(Base, self).__init__()

        self.id = id
        self.host = host


class WaitingList(Base):
    """ Log the email, time and ipaddr
        If we get another request from same ipaddr
    """

    __tablename__ = 'waitinglist'

    email = sqla.Column(sqla.Unicode(255), primary_key=True)
    ipaddr = sqla.Column(sqla.Unicode(255))
    requested = sqla.Column(sqla.DateTime)
    accepted = sqla.Column(sqla.DateTime)
    completed = sqla.Column(sqla.Boolean, default=False)

    def __init__(self, email, ipaddr=None):
        super(Base, self).__init__()
        self.email = email
        self.ipaddr = ipaddr
        self.requested = datetime.datetime.now()


class Error(Base):
    """ Log traceback """

    __tablename__ = 'errors'

    id = sqla.Column(sqla.Integer, 
                     sqla.Sequence('errors_seq'), primary_key=True)
    host = sqla.Column(sqla.Unicode(255))
    path = sqla.Column(sqla.Unicode())
    time = sqla.Column(sqla.DateTime)
    workingset = sqla.Column(sqla.Unicode())
    traceback = sqla.Column(sqla.Unicode())
    environ = sqla.Column(sqla.Unicode())
    fixed = sqla.Column(sqla.Boolean, default=False)

    def __init__(self, host, workingset, traceback):
        super(Error, self).__init__()
        self.host = host
        self.workingset = workingset
        self.traceback = traceback
        self.time = datetime.datetime.now()


@config.subscriber(config.SettingsInitialized)
def initialize(ev):
    # Create all tables
    Base.metadata.create_all()

    # Commit changes
    transaction.commit()
