import pandas as pd
import datapane as dp
from decouple import config
from modules.database import Database


class Datapane:
    """ Classe utilizada para publicações no Datapane.
     Acesse https://datapane.com/getting-started/ .
     """

    dp.login(token=config('DATAPANE_TOKEN'))

    @staticmethod
    def atualizar_relatorio(report=None):
        report = report
        # publica o relatório principal, se outro não for indicado
        if report is None:
            relatorios = Relatorios()
            report = relatorios.principal
        # publicação
        report.upload(name='colecao')


class Relatorios:

    def __init__(self):
        self.principal = Relatorios.relatorio_principal()

    @staticmethod
    def relatorio_principal():

        # localização dos jogos
        locais = Database.get_table(Database.tb_locais)
        # monta um plot para visualização de jogos por local
        x = locais['local'].value_counts().to_frame('Total')
        y = round((locais['local'].value_counts(normalize=True).to_frame('%') * 100), 1)
        locais_resumo = pd.concat([x, y], axis=1)
        locais_plot = locais_resumo.T.plot(kind='bar', figsize=(10, 5), layout=(3, 1), rot=0, fontsize=14)

        # criação do relatório
        report = dp.Report(
            "### Coleção de boardgames",

            dp.Group(
                dp.Select(blocks=[
                    dp.Plot(locais_plot, label='Gráfico'),
                    dp.DataTable(locais_resumo, label='Tabela', caption='Resumo de jogos por localização')
                ]),
                dp.DataTable(locais, caption="Jogos por localização"),
                columns=2
            )
        )

        return report