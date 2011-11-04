""" wsgi application setup """
import memphis.app
from memphis import view
from pyramid.config import Configurator


def app(global_config, **settings):
    """ wsgi app initialization """

    def getRoot(request, root=view.Root):
        return root

    # configuration
    config = Configurator(root_factory=getRoot, settings=settings)

    # memphis initialization
    memphis.app.initMemphis('ploud.frontend', config, global_config)
   
    return config.make_wsgi_app()
