import logging,logging.config
import yaml

def configure(config='config.yaml', loggerName='dev'):
    try:
        f = open(config, 'r')
        conf = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
    
        logging.config.dictConfig(conf['logging'])
        logger = logging.getLogger(loggerName)

        return conf,logger 
    except IOError:
        # return no configuration and default logger
        logging.error("IOError in init.py")
        return None,logging

    except Exception as e:
        logging.error("Uncaught Exception in init.py")
        print(e)
