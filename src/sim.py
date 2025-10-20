import pandas as pd
import re
from io import StringIO
import numpy as np

class Indexes:

    @staticmethod
    def IP_CAMARA(df):
        peso_pratica = peso_pratica = np.where(df['ch_pratica'] > 0, 1.2, 1)
        df['IP'] = (df['prop_matriculados'] * df['prop_ch_total'] * (1+df['prop_pre_requisito'])*peso_pratica) / df['prop_forca_trabalho']
        df['IP'] = df['IP'].replace([np.inf, -np.inf], 0).fillna(0)
        df['IP'] = df['IP']/df['IP'].sum()
        df = df.sort_values(by='IP', ascending=False)
        return df

    @staticmethod
    def IP_COMPONENTE(df):
        peso_pratica = peso_pratica = np.where(df['ch_pratica'] > 0, 1.2, 1)
        df['IP'] = ((df['prop_matriculados'] * df['prop_ch_total'] * (1+df['prop_pre_requisito'])) * peso_pratica )/(df["prop_forca_trabalho"])
        df['IP'] = df['IP'].replace([np.inf, -np.inf], 0).fillna(0)
        df['IP'] = df['IP']/df['IP'].sum()
        df = df.sort_values(by='IP', ascending=False)
        return df
    
    @staticmethod
    def IP_TEORICA(df):
        df['IP'] = ((df['prop_matriculados'] * (df['ch_teorica']/df['ch_teorica'].sum()) * (1+df['prop_pre_requisito'])))/(df["prop_forca_trabalho"])
        df['IP'] = df['IP'].replace([np.inf, -np.inf], 0).fillna(0)
        df['IP'] = df['IP']/df['IP'].sum()
        df = df.sort_values(by='IP', ascending=False)
        return df
    
class Simulator:

    def __init__(self, data, weights=None):
        self.data = data
        self.weights = weights
    
    def simulate_by_component(self, index_function, total, use_elective=False, min_by_project=0, xlsx_output_file=None):
        df = self.data.get_demand_by_component(use_elective)
        df = index_function(df)
        df = self.distribute(df, total, "IP", min_by_project)
        self.__write_xlsx(df, xlsx_output_file)
        print(df.to_string())
        return df
        #df.info()

    def simulate_by_area(self, index_function, total, use_elective=False, min_by_project=0, xlsx_output_file=None):
        df = self.data.get_demand_by_area(use_elective)
        df = index_function(df)
        df = self.distribute(df, total, "IP", min_by_project)
        print(df.to_string())
        self.__write_xlsx(df, xlsx_output_file)    
        return df
        #df.info()
    
    def simulate_by_area_and_practice(self, index_function, total, use_elective=False, min_by_project=0, xlsx_output_file=None):
        df = self.data.get_demand_by_area(use_elective)
        df = index_function(df)
        df, remaining = self.distribute_by_practice(df, total)
        df = self.distribute(df, remaining, "IP", min_by_project)
        print(df.to_string())
        self.__write_xlsx(df, xlsx_output_file)    

    def simulate_by_component_and_practice(self, index_function, total, use_elective=False, min_by_project=0, xlsx_output_file=None):
        df = self.data.get_demand_by_component(use_elective)
        df = index_function(df)
        df, remaining = self.distribute_by_practice(df, total)
        df = self.distribute(df, remaining, "IP", min_by_project)
        print(df.to_string())
        self.__write_xlsx(df, xlsx_output_file)    
    
    def __write_xlsx(self, df, xlsx_output_file=None):
        if xlsx_output_file is not None:
            df.to_excel(xlsx_output_file)

    def distribute_by_practice(self, df, total):
        df['bolsas_pratica'] = df['ch_pratica']/30/10
        df['bolsas_pratica'] = df['bolsas_pratica'].apply(np.ceil).astype(int)
        total -= int(df['bolsas_pratica'].sum())
        return df, total

    def distribute(self, df, total_bolsas, coluna_indice, min_by_project=0):
        df_result = df
        soma_total_indice = df_result[coluna_indice].sum()
        df_result['bolsas_total'] = 0
        if total_bolsas > df_result.shape[0]:
            df_result['bolsas_total'] = 1
        total_bolsas -= df_result.shape[0]

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
        return df_result