import pandas as pd
from modules.database import Database
from decouple import config
# noinspection PyUnresolvedReferences
from modules.fixpath import *  # DO NOT REMOVE
from submodules.ludopedia_wrapper import Ludopedia_API


class Colecao:

    def __init__(self):
        print(sys.path)
        self.ludopedia_api = Ludopedia_API.Ludopedia(conf_file=config('APP_CONF_PATH_SUBMODULE'))

    def atualizar_colecao(self):
        colecao = pd.DataFrame(self.ludopedia_api.buscar_colecao())
        Database.atualizar_database(colecao, Database.tb_colecao)
        print('Coleção atualizada.')
        return colecao


teste = Colecao()
teste.atualizar_colecao()
