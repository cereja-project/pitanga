import logging

import boto3

from pitanga.config.settings import Settings


class S3OperationError(Exception):
    pass


class S3Client:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            kwargs = {
                "region_name": Settings.AWS_DEFAULT_REGION,
            }
            if Settings.ENVIRONMENT == "localstack":
                # Se estiver rodando no ambiente localstack adiciona os parâmetros abaixo
                kwargs.update({
                    "aws_access_key_id":     Settings.AWS_ACCESS_KEY_ID,
                    "aws_secret_access_key": Settings.AWS_SECRET_ACCESS_KEY
                })
            cls._instance = boto3.client('s3', **kwargs)
        return cls._instance


class S3Operations:
    def __init__(self, bucket_name: str):
        self._s3 = S3Client()
        self._bucket_name = bucket_name

    @property
    def bucket_name(self):
        return self._bucket_name

    @property
    def client(self):
        return self._s3

    def upload_file(self, file_name: str, object_name: str = None):
        """
        Faz upload de um arquivo para o bucket S3.
        :param file_name: Caminho do arquivo a ser enviado.
        :param object_name: Nome do objeto no S3. Se não fornecido, file_name será usado.
        """
        if object_name is None:
            object_name = file_name
        try:
            self._s3.upload_file(file_name, self._bucket_name, object_name)
        except Exception as err:
            logging.error(f"Erro durante o upload do arquivo {file_name} para o bucket {self._bucket_name}")
            raise S3OperationError(err)

    def download_file(self, object_name: str, file_name: str):
        """
        Faz download de um arquivo do bucket S3.
        :param object_name: Nome do objeto no S3.
        :param file_name: Caminho local onde o arquivo será salvo.
        """
        try:
            self._s3.download_file(self._bucket_name, object_name, file_name)
        except Exception as err:
            logging.error(f"Erro durante o download do arquivo {object_name} do bucket {self._bucket_name}")
            raise S3OperationError(err)

    def delete_object(self, object_name: str):
        """
        Deleta um objeto específico do bucket S3.
        :param object_name: Nome do objeto no S3.
        """
        try:
            self._s3. \
                delete_object(Bucket=self._bucket_name, Key=object_name)
        except Exception as err:
            logging.error(f"Erro durante a remoção do objeto {object_name} no bucket {self._bucket_name}")
            raise S3OperationError(err)

    def list_objects(self, prefix: str = '') -> list:
        """
        Lista objetos no bucket S3.
        :param prefix: Prefixo para filtrar os objetos listados.
        :return: Lista de objetos.
        """
        try:
            response = self._s3.list_objects_v2(Bucket=self._bucket_name, Prefix=prefix)
            if 'Contents' in response:
                return response['Contents']
            return []
        except Exception as err:
            logging.error(f"Erro durante a listagem de objetos no bucket {self._bucket_name}")
            raise S3OperationError(err)

    def __str__(self):
        return f"S3Operations({self._bucket_name})"
