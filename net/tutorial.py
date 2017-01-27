import logging
import time

logging.basicConfig(level = logging.info,
                    format='(%(threadName)-10s) %(message)s')

def detonate_node(*args, **kwargs):
    """

    kwargs['target']: node to detonate
    kwargs['udf1']: amount of TNT to use (kg) 

    """

    node = kwargs['target']
    tnt = (kwargs['udf1'] if kwargs['udf1'] 
                            and type(kwargs['udf1']) is int 
                            and kwargs['udf1'] > 0 
                          else 1) 

    logging.info("Detonating node '%s' with %d kg TNT" % (node, tnt))


def electric_shock(*args, **kwargs):
    """

    kwargs['target']: node to shock 
    kwargs['udd']:  "volts" : voltage to be applied (V) 

    """

    node = kwargs['target']
    udd = kwargs['udd'] if 'udd' in kwargs else None
    voltage = udd['volts'] if udd and 'volts' in udd else 1 

    logging.info('Node: [%s] Shock applied [%d] V - Bzz, Bzz, ...' 
                 % (node, voltage))


def tranquilize(*args, **kwargs):
    """

    kwargs['target']: node to tranquilize 

    """

    node = kwargs['target']

    logging.info('Node: [%s] Zzz, Zzzzzz, ...' % node)


def revive(*args, **kwargs):
    """

    kwargs['target']: node to revive 

    """

    node = kwargs['target']

    logging.info("Node: [%s] Kickin' It" % node)


def nuclear_air_burst(*args, **kwargs):
    """

    """
    logging.info('Electromagnetic pulse in 10 seconds ...')
