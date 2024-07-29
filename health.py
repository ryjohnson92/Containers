
import gunicorn.app.base
import re
import os
import logging
import requests
import multiprocessing as mp
from flask import Flask
from flask_restful import Resource, Api


PORT = int(os.environ['HEALTHCHECK_PORT'])
class __app_base__:
    
    class GUNICORN_APP(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            
            self.application = app
            super().__init__()
        def load_config(self):
            config = {key: value for key, value in self.options.items()
                    if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    class health_check:
        def __init__(self) -> None:
            assert 'check' in dir(self), 'A healthcheck should have a check function which returns type bool'
            pass
        pass
    
    class health_handler():
      
        class health_check_json(Resource):
            def __init__(self, parent,app) -> None:
                self.parent = parent
                self.app = app
                super().__init__()
            def get(self):
                rets = {
                    "name":self.app.__class__.__name__,
                    "services":{

                    },
                    "metadata":{
                        "build": os.environ.get('BUILD_VERSION') if os.environ.get('BUILD_VERSION') else "unknown"
                    }
                }
                for check in self.parent.CHECKS:
                    try:
                        check_name = check
                        check = getattr(self.app,check_name)
                        rets["services"][check_name if not 'service' in dir(check) else check.service] = {
                            'name':check_name,
                            "status":"green" if check().check() else "red"
                        }
                    except Exception as err:
                        self.app.log.exception(err)
                for service in rets["services"]:
                    if rets["services"][service]["status"] != 'green':
                        rets['current_status'] = 'red'
                        break
                return rets
    
        def __init__(self,parent) -> None:
            self.PORT = PORT
            self.options = {
                'bind': '%s:%s' % ('0.0.0.0', self.PORT),
                'workers':2,
                # 'threads': number_of_workers(),
                'timeout': 7200
            }
  
            self.parent = parent ## bring parent into scope
            self.CHECKS = self.__build_checks__() ## build health checks
            self.app = Flask(__name__)
            self.api = Api(self.app)  
            self.api.add_resource(self.health_check_json,'/health_check.json',resource_class_kwargs={"parent":self,"app":self.parent})

        def __build_checks__(self):
            APP_CHECKS = []
            for x in dir(self.parent):
                if not re.match(r'__.*__',x,flags=re.I) and x != 'resource':
                    obj = getattr(self.parent,x)
                    if isinstance(obj, type):
                        if issubclass(obj,__app_base__.health_check) and obj != __app_base__.health_check:
                            try:
                                obj() ### Trigger assertion of correct check setup
                                APP_CHECKS.append(x)
                            except AssertionError as aserr:
                                self.parent.log.warn('Could not include check {} - {}'.format(x,str(aserr)))
            return APP_CHECKS

    def __init__(self,health_check_external:bool=False):
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s +0000] [%(process)d] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        self.log = logging.getLogger(self.__class__.__name__)
        assert 'entrypoint' in dir(self), 'Subclasses should contain an entrypoint function'
        self.health_handler = self.health_handler(self) 
        mp.set_start_method('fork', force=True)
        GAPP =  __app_base__.GUNICORN_APP(self.health_handler.app, self.health_handler.options)
        GUNICORNPROC = mp.Process(target =GAPP.run)
        GUNICORNPROC.start()
        try:
            if 'entrypoint' in dir(self):
                self.entrypoint()
        except Exception as err:
            self.log.exception(str(err))
        finally:
            self.log.warn("Killing application, Goodbye :)")
            GUNICORNPROC.kill()
            GUNICORNPROC.join()
            GUNICORNPROC.terminate()
            os.system('pkill -9 python3.11') ## :'( 

class Docker(__app_base__):
    def __init__(self, health_check_external: bool = False,**kwargs):
        super().__init__(health_check_external,**kwargs)
    
    @staticmethod
    def read_healthchecks():
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s +0000] [%(process)d] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        log = logging.getLogger('healthcheck')
        try:
            response = requests.get('http://127.0.0.1:{}/health_check.json'.format(str(PORT)))
            response = response.json()
            for service in response["services"]:
                assert response["services"][service]["status"] == 'green', 'Health check failed'
        except AssertionError as aserr:
            log.error(aserr)
            return 1
        except Exception as err:
            log.error(err)
            return 1