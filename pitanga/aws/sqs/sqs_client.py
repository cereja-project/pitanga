import logging
import math
from typing import Any

import boto3
from pitanga.config.settings import Settings


class SQSOperationError(Exception):
    pass


class SQSClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            kwargs = {
                "endpoint_url": Settings.SQS_ENDPOINT_URL,
                "region_name":  Settings.AWS_DEFAULT_REGION,
            }
            if Settings.ENVIRONMENT == "development":
                # Se estiver rodando no ambiente localstack adiciona os parâmetros abaixo
                kwargs.update({"aws_access_key_id":     Settings.AWS_ACCESS_KEY_ID,
                               "aws_secret_access_key": Settings.AWS_SECRET_ACCESS_KEY
                               })
            cls._instance = boto3.client('sqs', **kwargs)
        return cls._instance


class SQSOperations:
    def __init__(self, queue_name: str, max_number_to_consume: int = 10, wait_time_sec=20):
        self._sqs = SQSClient()
        self._queue_name = queue_name
        self._queue_url = self._sqs.get_queue_url(QueueName=self._queue_name)["QueueUrl"]
        self._max_number_to_consume = self._check_max_number_to_consume(max_number_to_consume)
        self._wait_time_sec = self._check_wait_time_sec(wait_time_sec)

    @property
    def queue_url(self):
        return self._queue_url

    @property
    def queue_name(self):
        return self._queue_name

    @property
    def client(self):
        return self._sqs

    @classmethod
    def _check_max_number_to_consume(cls, num):
        assert isinstance(num, (int, float)) and (10 >= num >= 1), \
            f"{num} não é um valor válido para max_number_of_messages. Envie um número entre 1 e 10. "
        return int(num)

    @classmethod
    def _check_wait_time_sec(cls, secs):
        assert isinstance(secs, (int, float)), f"{secs} não é um valor válido para wait_time_sec"
        return secs

    def _consume(self, max_number_to_consume: int, wait_time_sec: int):
        max_number_to_consume = self._check_max_number_to_consume(max_number_to_consume)
        messages = []
        response = self._sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_number_to_consume,
                WaitTimeSeconds=wait_time_sec
        )
        if 'Messages' in response:
            messages += response['Messages']
        return messages

    def consume_messages(self, max_number_to_consume: int = None, wait_time_sec: int = None) -> list:
        """
        Recupera mensagens da fila.

        :param max_number_to_consume: número inteiro entre 1 e 10 que determinará a quantidade de mensagens consumidas
                                      da fila.
        :param wait_time_sec: número inteiro que determina o tempo máximo de espera o resultado da fila.
        :return: lista de mensagens
        """
        try:
            max_number_to_consume = max_number_to_consume or self._max_number_to_consume

            messages = []
            wait_time_sec = self._check_wait_time_sec(wait_time_sec or self._wait_time_sec)
            for _ in range(math.floor(max_number_to_consume / self._max_number_to_consume)):
                messages += self._consume(self._max_number_to_consume, wait_time_sec)
                if len(messages) == 0:
                    # Não tem mensagens
                    return messages
            rest_to_complete = max_number_to_consume % self._max_number_to_consume
            if rest_to_complete > 0:
                messages += self._consume(rest_to_complete, wait_time_sec)
            return messages
        except Exception as err:
            logging.error(f"Erro ao consumir mensagens da fila {self._queue_name}")
            raise SQSOperationError(err)

    def send_message(self, message_body: Any):
        """
        Envia uma mensagem para a fila
        :param message_body: dado que será enviado, o valor será convertido para string.
        """
        try:
            self._sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=message_body if isinstance(message_body, str) else str(message_body)
            )
        except Exception as err:
            logging.error(f"Erro durante o envio de mensagem para a fila {self._queue_name}")
            raise SQSOperationError(err)

    def delete_message(self, receipt_handle):
        """
        Deleta uma mensagem específica da fila
        :param receipt_handle:
        :return:
        """
        try:
            self._sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
            )
        except Exception as err:
            logging.error(f"Erro durante a remoção de mensagem na fila {self._queue_name}")
            raise SQSOperationError(err)

    def purge(self):
        """
        Limpa completamente a fila
        """
        try:
            self._sqs.purge_queue(QueueUrl=self.queue_url)
        except Exception as err:
            logging.error(f"Erro durante a operação de limpeza da fila {self._queue_name}")
            raise SQSOperationError(err)

    def get_queue_length(self):
        """
        Retorna o número de mensagens na fila
        """
        try:
            attributes = self._sqs.get_queue_attributes(
                    QueueUrl=self._queue_url,
                    AttributeNames=['ApproximateNumberOfMessages']
            )
            return int(attributes['Attributes']['ApproximateNumberOfMessages'])
        except Exception as err:
            logging.error(f"Erro ao obter o tamanho da fila {self._queue_name}")
            raise SQSOperationError(err)

    def __str__(self):
        return f"SQSOperations({self._queue_name})"
