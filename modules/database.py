# bibliotecas
import pandas as pd
import psycopg2 as pg
# módulos externos
from decouple import config
from sqlalchemy import create_engine
from datetime import datetime


class Database:
    """ Classe para operação do banco de dados. """

    _host = config('DB_HOST')
    _name = config('DB_NAME')
    _user = config('DB_USER')
    _password = config('DB_PASS')
    _port = config('DB_PORT')

    # tablenames
    tb_colecao = 'colecao'
    tb_valor_de_mercado = 'jogos_valordemercado'

    @staticmethod
    def _connection(host=_host, name=_name, user=_user, password=_password):
        """ Conecta com o banco de dados. """
        connection = pg.connect(host=host, database=name, user=user, password=password)
        return connection

    @staticmethod
    def _engine(host=_host, name=_name, user=_user, password=_password, port=_port):
        """ Conecta com o banco de dados. """
        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{name}')
        return engine

    @staticmethod
    def get(sql, host=_host, name=_name, user=_user, password=_password):
        connection = pg.connect(host=host, database=name, user=user, password=password)
        df = pd.read_sql(sql, con=connection)
        return df

    @staticmethod
    def get_table(tablename, host=_host, name=_name, user=_user, password=_password):
        connection = pg.connect(host=host, database=name, user=user, password=password)
        sql = f'select * from {tablename}'
        df = pd.read_sql(sql, con=connection)
        return df

    @staticmethod
    def atualizar_database(df, tablename, if_exists='replace'):
        """ Grava um dataframe no banco de dados. """
        # grava o dataframe no banco de dados
        engine = Database._engine()
        df.to_sql(
            name=tablename,
            con=engine,
            if_exists=if_exists,
            index=False
        )
        engine.dispose()
        return df

    @staticmethod
    def insert_df(df, tablename, if_exists='append'):
        """ Grava um dataframe no banco de dados. """
        # grava o dataframe no banco de dados
        engine = Database._engine()
        df.to_sql(
            name=tablename,
            con=engine,
            if_exists=if_exists,
            index=False
        )
        # salva cópia de segurança
        Database.fazer_backup(df=df, tablename=tablename)
        engine.dispose()
        print('Valores adicionados.')

    @staticmethod
    def fazer_backup(df, tablename):
        filename = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
        df.to_csv(
            f"output/security_copy_{tablename}_{filename}.csv",
            sep=';',
            index=False
        )

    @staticmethod
    def verificar_existencia_de_tabela(tablename):
        sql = f"SELECT EXISTS ( SELECT FROM information_schema.tables WHERE table_name = '{tablename}');"
        engine = Database._engine()
        connection = engine.connect()
        result = connection.execute(sql).fetchall()[0][0]
        connection.close()
        engine.dispose()
        return result

    @staticmethod
    def execute(sql):
        engine = Database._engine()
        connection = engine.connect()
        connection.execute(sql)
        connection.close()
        engine.dispose()
