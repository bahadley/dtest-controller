import logging
import pika

logging.basicConfig(level = logging.info,
                    format='(%(threadName)-10s) %(message)s')

def send_msg(*args, **kwargs):
    """

    kwargs['target']: RabbitMQ node URI 
    kwargs['udf1']: RabbitMQ exhange to publish to 
    kwargs['udf2']: Msg topic 
    kwargs['udf3']: Msg body to deliver 

    """

    node = kwargs['target']
    exchange_name = (kwargs['udf1'] if kwargs['udf1'] and kwargs['udf1'] > 0
                               else "") 
    routing_key = (kwargs['udf2'] if kwargs['udf2'] and kwargs['udf2'] > 0
                            else "") 
    msg = (kwargs['udf3'] if kwargs['udf3'] and kwargs['udf3'] > 0
                          else "") 


    parameters = pika.URLParameters(node)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    channel.exchange_declare(exchange=exchange_name,
                             type='topic')


    channel.basic_publish(exchange=exchange_name,
                          routing_key=routing_key,
                          body=msg)

    connection.close()

    logging.info("Message sent to %s:%s:%s, body:  %s" % 
        (node, exchange_name, routing_key, msg))


def receive_msg(*args, **kwargs):
    """

    kwargs['target']: RabbitMQ node URI 
    kwargs['udf1']: RabbitMQ exhange to subscribe to 
    kwargs['udf2']: Topic to subscribe to

    """

    node = kwargs['target']
    exchange_name = (kwargs['udf1'] if kwargs['udf1'] and kwargs['udf1'] > 0
                               else "") 
    binding_key = (kwargs['udf2'] if kwargs['udf2'] and kwargs['udf2'] > 0
                            else "") 

    parameters = pika.URLParameters(node)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    channel.exchange_declare(exchange=exchange_name,
                             type='topic')

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=exchange_name,
                       queue=queue_name,
                       routing_key=binding_key)


    logging.info('Waiting for messages')
    def callback(ch, method, properties, body):
        logging.info("Message received: %r" % body)

    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True)

    channel.start_consuming()
