import pandas as pd
import numpy as np

class Indexes:
 
    @staticmethod
    def IP_TEORICA(df):
        df['IP'] = ((df['prop_matriculados'] * (df['ch_teorica']/df['ch_teorica'].sum()) *(1+df['prop_obrigatorio']) *(1+df['prop_pre_requisito'])))/(df["prop_forca_trabalho"])
        df['IP'] = df['IP'].replace([np.inf, -np.inf], 0).fillna(0)
        df['IP'] = df['IP']/df['IP'].sum()
        df = df.sort_values(by='IP', ascending=False)
        return df
    
class Simulator:

    def __init__(self, data, MAX_ANUAL_MONITOR=600):
        self.data = data
        self.MAX_ANUAL_MONITOR = MAX_ANUAL_MONITOR
   
    def simulate_by_area_and_practice(self, index_function, total, min_by_compulsory=0, min_by_project=0, xlsx_output_file=None):
        df = self.simulate_by_component_and_practice(
            index_function,
            total,
            min_by_compulsory=min_by_compulsory,
            min_by_project=min_by_project,
            xlsx_output_file=xlsx_output_file
        )
        df = df.groupby('camara').agg(
            matriculados      = ('matriculados', 'sum'),
            n_turmas          = ('n_turmas', 'sum'),
            n_subturmas       = ('n_subturmas', 'sum'),
            ch_teorica        = ('ch_teorica', 'sum'),
            ch_pratica        = ('ch_pratica', 'sum'),
            ch_total          = ('ch_total', 'sum'),
            obrigatorio_generalista = ('obrigatorio_generalista', 'sum'),
            obrigatorio_enfase = ('obrigatorio_enfase', 'mean'),
            pre_requisito     = ('pre_requisito', 'sum'),
            n_professores     = ('n_professores', 'first'),
            n_componentes     = ('n_componentes', 'count'),
            prop_matriculados = ('prop_matriculados', 'sum'),
            prop_ch_total     = ('prop_ch_total', 'sum'),
            prop_pre_requisito = ('prop_pre_requisito', 'sum'),
            prop_forca_trabalho = ('prop_forca_trabalho', 'first'),
            prop_obrigatorio  = ('prop_obrigatorio', 'mean'),
            IP                = ('IP', 'sum'),
            bolsas_pratica    = ('bolsas_pratica', 'sum'),
            bolsas_teorica    = ('bolsas_teorica', 'sum'),
            bolsas_total      = ('bolsas_total', 'sum')
        ).reset_index()
        df = df.rename(columns={'camara': 'titulo'})
        df = df.sort_values(by="bolsas_total", ascending=False)
        self.__write_xlsx(df, xlsx_output_file)
        return df

    def simulate_by_component_and_practice(self, index_function, total, min_by_compulsory=0, min_by_project=0, xlsx_output_file=None):
        df = self.data.get_demand_by_component(use_elective=False)
        df = index_function(df)
        df, remaining = self.distribute_by_practice(df, total)
        df = self.distribute(df, remaining, "IP", min_by_compulsory=min_by_compulsory, min_by_project=min_by_project)
        df = df.sort_values(by="bolsas_total", ascending=False)
        self.__write_xlsx(df, xlsx_output_file)
        return df

    def __write_xlsx(self, df, xlsx_output_file=None):
        if xlsx_output_file is not None:
            df.to_excel(xlsx_output_file)

    def distribute_by_practice(self, df, total):
        df['bolsas_pratica'] = np.where(df['ch_pratica_base'] > 0, df['ch_pratica'] / self.MAX_ANUAL_MONITOR, 0)
        df['bolsas_pratica'] = df['bolsas_pratica'].apply(np.ceil).astype(int)
        necessidade_pratica = df['bolsas_pratica'].sum()
        if necessidade_pratica > total:
            print(f"AVISO: Necessidade de bolsas de prática ({necessidade_pratica}) excede o total ({total}).")
            print("Distribuindo todas as bolsas disponíveis para a prática.")
            if necessidade_pratica > 0:
                proporcao_necessidade = df['bolsas_pratica'] / necessidade_pratica
                df['bolsas_pratica'] = (proporcao_necessidade * total).apply(np.floor).astype(int)
                restantes = total - df['bolsas_pratica'].sum()
                if restantes > 0:
                    residuos = (proporcao_necessidade * total) - df['bolsas_pratica']
                    indices_maiores = residuos.nlargest(restantes).index
                    df.loc[indices_maiores, 'bolsas_pratica'] += 1
            else:
                df['bolsas_pratica'] = 0
        bolsas_alocadas = int(df['bolsas_pratica'].sum())
        remaining = max(0, total - bolsas_alocadas)
        return df, remaining

    def distribute(self, df, total_bolsas, coluna_indice, min_by_compulsory=0, min_by_project=0):
        df_result = df
        soma_total_indice = df_result[coluna_indice].sum()
        df_result['bolsas_total'] = 0
        if total_bolsas > np.sum(df_result['obrigatorio_generalista']==1) and min_by_compulsory > 0:
            df_result['bolsas_total'] = np.where((df['obrigatorio_generalista'] ==1) & (df['matriculados'] != 0)  , 1, 0)
        total_bolsas -= df_result['bolsas_total'].sum()
        if soma_total_indice == 0:
            df_result['bolsas_total'] = 0
            return df_result
        df_result['proporcao'] = df_result[coluna_indice] / soma_total_indice
        df_result['alocacao_ideal'] = df_result['proporcao'] * total_bolsas
        df_result['alocacao_base'] = df_result['alocacao_ideal'].apply(np.floor).astype(int)
        df_result['residuo'] = df_result['alocacao_ideal'] - df_result['alocacao_base']
        bolsas_alocadas_base = df_result['alocacao_base'].sum()
        bolsas_restantes = total_bolsas - bolsas_alocadas_base
        df_result['bolsas_total'] = df_result['bolsas_total']+ df_result['alocacao_base']
        if bolsas_restantes > 0:
            indices_maiores_residuos = df_result['residuo'].nlargest(bolsas_restantes).index
            df_result.loc[indices_maiores_residuos, 'bolsas_total'] += 1
        df_result.drop(columns=['proporcao', 'alocacao_ideal', 'alocacao_base', 'residuo'], inplace=True)
        if 'bolsas_pratica' in df_result.columns:
            df_result['bolsas_teorica'] = df['bolsas_total']
            df_result['bolsas_total'] = df_result['bolsas_total'] + df_result['bolsas_pratica']
            colunas = list(df.columns)
            colunas[colunas.index("bolsas_total")], colunas[colunas.index("bolsas_teorica")] = "bolsas_teorica", "bolsas_total"
            df_result = df_result[colunas]
        return df_result