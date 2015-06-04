import logging,logging.config
import yaml

def configure(config='config.yaml', loggerName='dev'):
    try:
        f = file(config, 'r')
        conf = yaml.load(f)
        f.close()
    
        logging.config.dictConfig(conf['logging'])
        logger = logging.getLogger(loggerName)
   
        return conf,logger 
    except IOError:
        # return no configuration and default logger
        logging.error("IOError in init.py")
        return None,logging

    except:
        logging.error("Uncaught Exception in init.py")
