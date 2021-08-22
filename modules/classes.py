# BIBLIOTECAS E MÓDULOS EXTERNOS
import pandas as pd
from modules.database import Database
from decouple import config
from datetime import datetime

# MÓDULOS INTERNOS E SUBMÓDULOS
# noinspection PyUnresolvedReferences
from modules.fixpath import *  # DO NOT REMOVE
from submodules.ludopedia_wrapper import Ludopedia_API
from submodules.buscador.src.modules.scrapper import Scrapper
from submodules.buscador.src.modules.service import Service


class Colecao:

    @staticmethod
    def _acessar_api_ludopedia():
        ludopedia_api = Ludopedia_API.Ludopedia(conf_file=config('APP_CONF_PATH_SUBMODULE'))
        return ludopedia_api

    @staticmethod
    def atualizar_colecao():
        ludopedia_api = Colecao._acessar_api_ludopedia()
        colecao = pd.DataFrame(ludopedia_api.buscar_colecao())
        Database.atualizar_database(colecao, Database.tb_colecao)
        print('Coleção atualizada.')
        return colecao

    @staticmethod
    def buscar_colecao():
        df = Database.get_table(Database.tb_colecao)
        return df


class Mercado:

    @staticmethod
    def valor_atual_de_boardgame(nome_do_boardgame):
        """ Busca valor de mercado. É utilizado o serviço da Compara Jogos e um scrapper de anúncios na Ludopedia. """
        valor_atual = Mercado.encontra_valor_atual_em_comparajogos(nome_do_boardgame)
        if valor_atual is None:
            valor_atual = Mercado.calcula_valor_medio_na_ludopedia(nome_do_boardgame)
        if config('DEBUG', cast=bool) and valor_atual is None:
            print(f'Valor não encontrado.')
        return valor_atual

    @staticmethod
    def encontra_valor_atual_em_comparajogos(nome_do_boardgame):
        """ Busca valor de mercado em Compara Jogos. """
        if config('DEBUG', cast=bool):
            print(f'Buscando boardgame {nome_do_boardgame} em Compara Jogos.')
        comparajogos = Service()
        response = comparajogos.busca_preco_medio(boardgame=nome_do_boardgame)
        valor_atual = response['preco']
        if config('DEBUG', cast=bool):
            print(f'Valor: {valor_atual} em Compara Jogos.')
        return valor_atual

    @staticmethod
    def calcula_valor_medio_na_ludopedia(nome_do_boardgame):
        """ Realiza scrapper de anúncios na Ludopedia para calcular valor médio. """
        if config('DEBUG', cast=bool):
            print(f'Buscando boardgame {nome_do_boardgame} em Ludopedia.')
        anuncios = Mercado.buscar_anuncios_na_ludopedia(nome_do_boardgame)
        # cálculo de mediana dos valores resultados
        # realizado somente se há registros na resposta do scrapper
        if len(anuncios):
            df = pd.DataFrame(anuncios)
            df.value = df.value.apply(lambda x: x.replace('R$ ', '').replace('.', '').replace(',', '.'))
            eh_jogo = df['name'] == nome_do_boardgame
            eh_venda = df['category'] == 'Venda'
            df_filtrado = df[eh_jogo & eh_venda]
            valor_medio = round(df_filtrado.value.median(), 2)
            if config('DEBUG', cast=bool):
                print(f'Valor: {valor_medio} em Ludopedia.')
            return valor_medio
            # retorna null se não há resultados no scrapper
        else:
            valor_medio = None
            if config('DEBUG', cast=bool):
                print(f'Valor: {valor_medio} em Ludopedia.')
            return None

    @staticmethod
    def buscar_anuncios_na_ludopedia(nome_do_boardgame, tipo=None):
        """ Retorna um DataFrame com os anúncios obtidos na Ludopedia. """
        # objeto e resposta de scrapper no site da Ludopedia
        ludopedia_scrapper = Scrapper()
        response = ludopedia_scrapper.scrap_anuncios(nome_do_boardgame)
        # monta um dataframe com a resposta
        df = pd.DataFrame(response)
        # habilita parâmetro para filtrar por tipo de anúncia (a princípio, Venda ou Leilão)
        if tipo is not None:
            df = df[df['category'] == tipo]
        # retorna um dataframe
        return df

    @staticmethod
    def _construir_valor_atual():
        """ Constroi a tabela de DB com valores registrados dos jogos, se ela não existir. """
        # impede construir caso tabela já exista, evitando eliminar dados
        if Database.verificar_existencia_de_tabela(Database.tb_valor_de_mercado):
            # retorna aviso se a tabela já existir e encerra
            warning = 'Tabela de valores registrados já existe. Use método para atualizar'
            return warning
        # constroi a tabela
        else:
            colecao = Colecao.buscar_colecao()
            df = colecao[['id_jogo', 'nm_jogo']]
            df['valor_de_mercado'] = df['nm_jogo'].apply(lambda jogo: Mercado.valor_atual_de_boardgame(jogo))
            today = datetime.now().strftime("%d/%m/%Y")
            df['ultima_atualizacao'] = today
            Database.atualizar_database(df, Database.tb_valor_de_mercado)
            print('Tabela criada.')
            return df

    @staticmethod
    def buscar_valores_registrados():
        """ Busca a tabela com valores registrados dos jogos. """
        # verifica se tabela existe, e se não existir a constroi
        if not Database.verificar_existencia_de_tabela(Database.tb_valor_de_mercado):
            # constroi na DB tabela com valores atuais
            Mercado._construir_valor_atual()
        # consulta DB e retorna tabela
        df = Database.get_table(Database.tb_valor_de_mercado)
        return df

    @staticmethod
    def _atualizar_jogos_registrados():
        """ Acrescenta na tabela de registros os jogos eventualmente faltantes. """
        registrados_atuais = Mercado.buscar_valores_registrados()[['id_jogo', 'nm_jogo']]
        colecao_atual = Colecao.buscar_colecao()[['id_jogo', 'nm_jogo']]
        contraselecao = colecao_atual['id_jogo'].isin(registrados_atuais['id_jogo'].to_list())
        nao_registrados = colecao_atual[~contraselecao]
        Database.insert_df(nao_registrados, Database.tb_valor_de_mercado)

    @staticmethod
    def _atualizar_registro_de_valor(row):
        """ A partir de uma das linhas da tabela de valores registrados, atualiza o valor atual. """
        # cria variáveis básicas necessárias
        data_de_hoje = datetime.now().strftime("%d/%m/%Y")
        nome_do_boardgame = row['nm_jogo']
        # id_do_boardgame = row['id_jogo']
        valor_atual = Mercado.valor_atual_de_boardgame(nome_do_boardgame)
        # preserva valor anterior, se o atual for nulo
        if (valor_atual is not None) or (row['ultima_atualizacao'] is None):
            row['ultima_atualizacao'] = data_de_hoje
            row['valor_de_mercado'] = valor_atual
        return row

    @staticmethod
    def atualizar_valores_registrados():
        """ Atualiza a tabela de valores registras para os jogos. """
        Mercado._atualizar_jogos_registrados()
        registrados_atuais = Mercado.buscar_valores_registrados()
        novos_registros = registrados_atuais.apply(lambda row: Mercado._atualizar_registro_de_valor(row), axis=1)
        Database.atualizar_database(novos_registros, Database.tb_valor_de_mercado)
        print('Valores atualizados')
