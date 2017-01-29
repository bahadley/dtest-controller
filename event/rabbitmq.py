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

    channel.exchange_declare(exchange='logs',
                             type='fanout')


    channel.basic_publish(exchange='logs',
                          routing_key='',
                          body=msg)

    connection.close()

    logging.info("Message sent to '%s', body:  %s" % (node, msg))


def receive_msg(*args, **kwargs):
    """

    kwargs['target']: RabbitMQ node URI 

    """

    node = kwargs['target']

    parameters = pika.URLParameters(node)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    channel.exchange_declare(exchange='logs',
                             type='fanout')

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='logs',
                       queue=queue_name)


    logging.info('Waiting for messages')
    def callback(ch, method, properties, body):
        logging.info("Message received: %r" % body)

    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True)

    channel.start_consuming()
