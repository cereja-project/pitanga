import logging
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Union

import psycopg2
from psycopg2 import sql, pool
from ..config.settings import Settings


class DataBaseUpdateError(Exception):
    """Exceção personalizada para erros de atualização do banco de dados."""
    pass


class InvalidQueryError(Exception):
    """Exceção personalizada para consultas SQL inválidas."""
    pass


class DatabaseConnection:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def connect(self):
        """Conecta ao banco de dados e cria um pool de conexões."""
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.SimpleConnectionPool(
                        1, 20,  # minconn, maxconn
                        database=Settings.POSTGRES_DB,
                        user=Settings.POSTGRES_USER,
                        password=Settings.POSTGRES_PASSWORD,
                        host=Settings.POSTGRES_HOST,
                        port=Settings.POSTGRES_PORT,
                        options='-c timezone=America/Sao_Paulo'
                )
            except (Exception, psycopg2.Error) as error:
                logging.error(f"Erro ao conectar ao banco de dados: {error}")
                raise psycopg2.Error(f"{error}: Erro ao conectar ao banco de dados.")

    def get_connection(self):
        """Obtém uma conexão do pool de conexões."""
        self.connect()
        return self._pool.getconn()

    def release_connection(self, connection):
        """Libera uma conexão de volta ao pool de conexões.

        Args:
            connection: Conexão do banco de dados a ser liberada.
        """
        self._pool.putconn(connection)

    def close_all(self):
        """Fecha todas as conexões no pool de conexões."""
        if self._pool:
            self._pool.closeall()


class DatabaseOperations:

    def __init__(self, query_batch_size=None):
        """Inicializa a classe com um pool de conexões e tamanho do lote para consultas.

        Args:
            query_batch_size (int, optional): Tamanho do lote para consultas. Se não fornecido, usa o valor padrão das configurações.
        """
        self.db_conn = DatabaseConnection()
        self.query_batch_size = query_batch_size or Settings.DB_QUERY_BATCH_SIZE

    def _validate_query_type(self, query, expected_type):
        """Valida se o tipo de consulta SQL corresponde ao tipo esperado.

        Args:
            query (str): A consulta SQL a ser validada.
            expected_type (str): O tipo de consulta SQL esperado (ex: "SELECT", "UPDATE", "DELETE").

        Raises:
            InvalidQueryError: Se a consulta não corresponder ao tipo esperado.
        """
        if not query.strip().upper().startswith(expected_type):
            raise InvalidQueryError(f"Expected a {expected_type} query.")

    def _execute_query(self, query, *params, commit=False):
        """Executa uma consulta SQL com os parâmetros fornecidos e opcionalmente comita a transação.

        Args:
            query (str): A consulta SQL a ser executada.
            *params: Parâmetros para a consulta SQL.
            commit (bool, optional): Se True, comita a transação após executar a consulta. Padrão é False.

        Returns:
            list: Resultados da consulta, se houver.

        Raises:
            DataBaseUpdateError: Se ocorrer um erro durante a execução da consulta.
        """
        conn = self.db_conn.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL(query), *params)
                result = cursor.fetchall() if cursor.description else None
                if commit:
                    conn.commit()
                return result
        except Exception as err:
            conn.rollback()
            logging.error(f"Erro durante a consulta no banco: {err}")
            raise DataBaseUpdateError(f"Erro durante a consulta no banco: {err}")
        finally:
            self.db_conn.release_connection(conn)

    @staticmethod
    def replace_query_with_count(sql_query):
        """Substitui a consulta SQL por uma consulta que conta o número de registros.

        Args:
            sql_query (str): A consulta SQL original.

        Returns:
            str: A consulta SQL modificada para contar registros.
        """
        # Remove comentários SQL
        sql_query = re.sub(r'--.*?\n|/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        # Remove cláusulas ORDER BY
        sql_query = re.sub(r'(?i)\border\s+by\b.*?(?=($|;|\)))', '', sql_query, flags=re.DOTALL)

        pattern = re.compile(r'(?i)\bSELECT\b')
        match = pattern.search(sql_query)
        if not match:
            return sql_query

        select_index = match.start()
        subquery_level = 0
        from_index = select_index

        while from_index < len(sql_query):
            if sql_query[from_index:from_index + 4].upper() == 'FROM' and subquery_level == 0:
                break
            if sql_query[from_index] == '(':
                subquery_level += 1
            elif sql_query[from_index] == ')':
                subquery_level -= 1
            from_index += 1

        # Verifica se a cláusula DISTINCT está presente
        distinct_pattern = re.compile(r'(?i)\bDISTINCT\b')
        if distinct_pattern.search(sql_query[select_index:from_index]):
            # Encapsula a consulta original em uma subconsulta
            result_query = f'SELECT COUNT(*) FROM (SELECT {sql_query[select_index + 7:]}) AS subquery'
        else:
            result_query = f'SELECT COUNT(*) {sql_query[from_index:]}'

        return re.sub("[\t\n\r\x0b\x0c ]+", " ", result_query).strip()  # remove espaços em branco desnecessários.

    def _get_total_records(self, query, *params):
        """Obtém o número total de registros para a consulta SQL fornecida.

        Args:
            query (str): A consulta SQL para contar registros.
            *params: Parâmetros para a consulta SQL.

        Returns:
            int: O número total de registros.
        """
        result = self._execute_query(self.replace_query_with_count(query), params)
        if not result:
            return 0
        total_records = result[0][0]
        return total_records

    def count_total_records(self, query, *query_params):
        """Conta o número total de registros para a consulta SELECT fornecida.

        Args:
            query (str): A consulta SELECT para contar registros.
            *query_params: Parâmetros para a consulta SQL.

        Returns:
            int: O número total de registros.
        """
        self._validate_query_type(query, "SELECT")
        return self._get_total_records(query, *query_params)

    def select(self, query: str, *query_params, batch_size=None, on_fetch=None) -> Union[list, None]:
        """Executa uma consulta SELECT em lotes e aplica uma função de callback aos resultados.

        Args:
            query (str): A consulta SELECT a ser executada.
            *query_params: Parâmetros para a consulta SQL.
            batch_size (int, optional): Tamanho do lote para a consulta. Se não fornecido, usa o valor padrão.
            on_fetch (callable, optional): Função de callback para processar cada lote de resultados. Se não fornecido, retorna uma lista com os resultados.

        Returns:
            list or None: Lista de resultados se on_fetch não for fornecido, caso contrário, None.
        """
        self._validate_query_type(query, "SELECT")
        t0 = time.time()
        result = None
        if on_fetch is None:
            # Se não enviar função de callback então irá criar uma lista para armazenar o resultado.
            result = []
            on_fetch = result.append
        total_records = self._get_total_records(query, *query_params)
        if total_records == 0:
            logging.info("SEM REGISTRO")
            return on_fetch([])

        batch_size = batch_size or (math.ceil(total_records / Settings.NUM_WORKERS)
                                    if self.query_batch_size == -1
                                    else self.query_batch_size)
        query = f"""
        {query}
        LIMIT %s OFFSET %s
        """

        with ThreadPoolExecutor(max_workers=Settings.NUM_WORKERS) as executor:
            futures = [executor.submit(self._execute_query, query, (*query_params, batch_size, offset))
                       for offset in range(0, total_records, batch_size)]

            total_finished = 0
            for future in as_completed(futures):
                data = future.result()
                on_fetch(data)
                total_finished += len(data)
                logging.info(f"Finalizados: {total_finished}/{total_records} - Duração: {round(time.time() - t0, 2)}s")
        return result

    def update(self, query: str, *query_params):
        """Executa uma consulta UPDATE no banco de dados.

        Args:
            query (str): A consulta UPDATE a ser executada.
            *query_params: Parâmetros para a consulta SQL.
        """
        self._validate_query_type(query, "UPDATE")
        t0 = time.time()
        try:
            self._execute_query(query, *query_params, commit=True)
            logging.info(f"Update executado em {round(time.time() - t0, 2)} segundos")
        except DataBaseUpdateError as e:
            logging.error(f"Erro ao executar update: {e}")

    def delete(self, query: str, *query_params):
        """Executa uma consulta DELETE no banco de dados.

        Args:
            query (str): A consulta DELETE a ser executada.
            *query_params: Parâmetros para a consulta SQL.
        """
        self._validate_query_type(query, "DELETE")
        t0 = time.time()
        try:
            self._execute_query(query, *query_params, commit=True)
            logging.info(f"Delete executado em {round(time.time() - t0, 2)} segundos")
        except DataBaseUpdateError as e:
            logging.error(f"Erro ao executar delete: {e}")

    def close_connection(self):
        """Fecha todas as conexões no pool de conexões."""
        self.db_conn.close_all()
