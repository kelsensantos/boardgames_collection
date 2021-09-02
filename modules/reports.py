import datapane as dp
from decouple import config


class Datapane:
    """ Classe utilizada para publicações no Datapane.
     Acesse https://datapane.com/getting-started/ .
     """

    dp.login(token=config('DATAPANE_TOKEN'))

    @staticmethod
    def atualizar_relatorio(report, titulo):
        report.upload(name=titulo)
