import logging
import subprocess

logging.basicConfig(level = logging.info,
                    format='(%(threadName)-10s) %(message)s')

def kill_leader(*args, **kwargs):
    """
    kwargs['target']:  Linux process to kill
    kwargs['udf1']:  Signal to send to pkill 
    """

    node = kwargs['target']
    signal = (kwargs['udf1'] if kwargs['udf1'] and kwargs['udf1'] > 0
                               else "") 

    subprocess.call(["pkill", signal, "-f", "-u", "root", node])

    logging.info("Process killed: %s" % node)
