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

    _ludopedia_api = Ludopedia_API.Ludopedia(conf_file=config('APP_CONF_PATH_SUBMODULE'))

    @staticmethod
    def _acessar_api_ludopedia():
        ludopedia_api = Ludopedia_API.Ludopedia(conf_file=config('APP_CONF_PATH_SUBMODULE'))
        return ludopedia_api

    @staticmethod
    def _atualizar_tags_de_jogos(colecao):
        df = colecao[['id_jogo', 'nm_jogo']]
        api = Colecao._ludopedia_api
        df['tags'] = df['id_jogo'].apply(lambda __id: api.buscar_jogo_na_colecao(__id, retornar_somente_tags=True))
        Database.atualizar_database(df, Database.tb_tags)

    @staticmethod
    def _atualiza_locais_dos_jogos(colecao):
        """ Para esse método funcionar, é necessário que hajam tags iniciadas com a indicação 'local:'. """
        api = Colecao._ludopedia_api
        # consulta tags na ludopedia
        tags = pd.DataFrame(api.get_endpoint('/colecao/tags')['tags'])
        # consulta tags com identificação de local
        locais_df = tags[tags.nm_tag.str.contains('local:')]
        # prossegue se houver tags de marcação de local
        # busca jogos com tags
        tags_por_jogo = Database.get_table(Database.tb_tags)
        if len(locais_df):
            # isola nome das tags em lista
            locais = locais_df.nm_tag.str.replace('local:', '')
            locais = locais.str.strip()
            dfs_to_concat = []
            for local in locais:
                df = tags_por_jogo[tags_por_jogo.tags.str.contains(local)].copy()
                df['local'] = local
                df = df[['local', 'nm_jogo', 'id_jogo']]
                dfs_to_concat.append(df)
            df_com_local = pd.concat(dfs_to_concat)
            # identificando jogos sem local definido
            contraselecao = colecao['id_jogo'].isin(df_com_local['id_jogo'])
            locais_nao_definidos = colecao[~contraselecao].copy()
            locais_nao_definidos['local'] = 'não definido'
            locais_nao_definidos = locais_nao_definidos[['local', 'nm_jogo', 'id_jogo']]
            # concatena os dataframes
            df = pd.concat([df_com_local, locais_nao_definidos])
        else:
            df = colecao[['nm_jogo', 'id_jogo']].copy()
            df['local'] = 'não definido'
        # salva no banco de dados
        Database.atualizar_database(df, Database.tb_locais)

    @staticmethod
    def _atualiza_detalhes_dos_jogos(colecao):
        api = Colecao._ludopedia_api
        detalhes = colecao['id_jogo'].apply(lambda x: api.buscar_jogo_detalhes(x))
        df = pd.DataFrame(list(detalhes))
        # corrige dtypes
        df = df.astype({
            'mecanicas': str,
            'temas': str,
            'artistas': str,
            'designers': str,
            'categorias': str
        })
        # salva no banco de dados
        Database.atualizar_database(df, Database.tb_jogos_detalhes)

    # noinspection PyBroadException
    @staticmethod
    def _atualiza_dados_privados(colecao):

        def obtem_dados(row, valores):
            # obtém comentário privado
            comentario = row['comentario_privado']
            if comentario is not None:
                # separa as linhas em lista
                x = comentario.split(sep='\n')
                # elimina strings vazias
                x = list(filter(None, x))
                # elimina eventuais espaços adicionais
                x = [i.strip() for i in x]
            # cria dicionário a ser preenchido e preenche dados de identificação e custo do jogo
            dados = {'id_jogo': row.id_jogo, 'nm_jogo': row.nm_jogo, 'vl_custo': row.vl_custo}
            # preenche dados de custo e valor de mercado (se existir na database)
            if valores is not False:
                selecao = valores['id_jogo'] == row['id_jogo']
                dados_jogo = valores[selecao]
                vl_mercado = dados_jogo['valor_de_mercado'].item()
                dados['vl_mercado'] = vl_mercado
            # preenche o dicionário com valores nas linhas
            if comentario is not None:
                # noinspection PyUnboundLocalVariable
                for v in x:
                    # obtém valores em cada linha
                    linha = v.split(sep=':')
                    # elimina eventuais espaços adicionais
                    linha = [i.strip() for i in linha]
                    # trata valores na lista
                    dados[linha[0]] = linha[1]
            dados_privados.append(dados)

        try:
            valores_atuais = Mercado.buscar_valores_registrados()
        except:
            valores_atuais = False

        dados_privados = []
        colecao.apply(lambda row: obtem_dados(row, valores_atuais), axis=1)
        df = pd.DataFrame(dados_privados)
        Database.atualizar_database(df, Database.tb_dados_privados)

    @staticmethod
    def atualizar_colecao(atualizar_valor_de_mercado=True):
        api = Colecao._ludopedia_api
        print('Atualizando coleção...')
        print('Buscando jogos na coleção...')
        colecao = pd.DataFrame(api.buscar_colecao())
        Database.atualizar_database(colecao, Database.tb_colecao)
        print('Atualizados jogos na coleção...')
        # atualiza tags dos jogos
        print('Buscando tags dos jogos...')
        Colecao._atualizar_tags_de_jogos(colecao)
        print('Atualizadas tags de usuário...')
        # atualiza local dos jogos
        print('Buscando localização dos jogos...')
        Colecao._atualiza_locais_dos_jogos(colecao)
        print('Atualizadas localizações dos jogos...')
        # atualiza detalhes dos jogos
        print('Buscando detalhes dos jogos...')
        Colecao._atualiza_detalhes_dos_jogos(colecao)
        # atualiza dados extras de usuários
        if atualizar_valor_de_mercado:
            print('Atualizando valores de mercado...')
            Mercado.atualizar_valores_registrados()
            print('Valor de mercado atualizado...')
        # atualiza dados privados da coleção
        print('Atualizando dados privados da coleção...')
        Colecao._atualiza_dados_privados(colecao)
        print('Dados privados da coleção atualizados...')
        # fim
        print('Atualização completa!')

    @staticmethod
    def buscar_colecao(jogo_base=False):
        df = Database.get_table(Database.tb_colecao)
        if jogo_base:
            jogos_detalhes = Database.get_table(Database.tb_jogos_detalhes)
            jogos_base = jogos_detalhes[jogos_detalhes['tp_jogo' == 'b']]
            selecao = df['id_jogo'].insin(list(jogos_base['id_jogo']))
            df = df[selecao]
        return df

    @staticmethod
    def buscar_localizacao_de_jogos():
        df = Database.get_table(Database.tb_locais)
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
        valor_registrado = row['valor_de_mercado']
        # preserva valor anterior, se o atual for nulo (e nunca foi atualizado e o registrado não é nulo)
        if (valor_atual is not None) or (row['ultima_atualizacao'] is None) or (valor_registrado is None):
            row['ultima_atualizacao'] = data_de_hoje
            row['valor_de_mercado'] = valor_registrado
        return row

    @staticmethod
    def atualizar_valores_registrados():
        """ Atualiza a tabela de valores registras para os jogos. """
        Mercado._atualizar_jogos_registrados()
        registrados_atuais = Mercado.buscar_valores_registrados()
        novos_registros = registrados_atuais.apply(lambda row: Mercado._atualizar_registro_de_valor(row), axis=1)
        Database.atualizar_database(novos_registros, Database.tb_valor_de_mercado)
        print('Valores atualizados')
        return novos_registros
