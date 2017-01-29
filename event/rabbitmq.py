import logging
import pika

logging.basicConfig(level = logging.info,
                    format='(%(threadName)-10s) %(message)s')

def send_msg(*args, **kwargs):
    """

    kwargs['target']: RabbitMQ node URI 
    kwargs['udf1']: msg body to deliver 

    """

    node = kwargs['target']
    msg = (kwargs['udf1'] if kwargs['udf1'] 
                            and kwargs['udf1'] > 0 
                          else "") 


    parameters = pika.URLParameters(node)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    channel.queue_declare(queue='hello')

    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body=msg)

    connection.close()

    logging.info("Message sent to '%s', body:  %d" % (node, msg))


def receive_msg(*args, **kwargs):
    """

    kwargs['target']: RabbitMQ node URI 

    """

    node = kwargs['target']

    parameters = pika.URLParameters(node)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
       logging.info("Message received '%s'" % body)

    channel.basic_consume(callback,
                          queue='hello',
                          no_ack=True)

    logging.info('Waiting for messages')
    channel.start_consuming()
