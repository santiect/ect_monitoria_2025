import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def generate_all_simulation_visualizations(df_component, df_area):
    """
    Gera um conjunto completo de gráficos com estilo profissional e unificado para
    analisar a demanda e os resultados da simulação.

    Args:
        df_component (pd.DataFrame): DataFrame da simulação por componente.
        df_area (pd.DataFrame): DataFrame da simulação por área.
    """
    # --- 1. CONFIGURAÇÃO GERAL DE ESTILO ---
    sns.set_theme(
        style="whitegrid",
        rc={
            "axes.facecolor": "#f5f5ff",
            "figure.facecolor": "white",
            "axes.edgecolor": ".8",
            "grid.color": ".9",
            "font.family": "sans-serif",
            "axes.labelweight": "bold",
        }
    )

    # --- 2. PALETA DE CORES E PARÂMETROS DE TAMANHO ---
    THEORY_COLOR = '#0077b6'
    PRACTICE_COLOR = '#f77f00'
    SINGLE_VALUE_PALETTE = 'crest'
    # Parâmetros de tamanho reduzidos para gráficos mais compactos
    INCH_PER_BAR = 0.5
    MIN_CHART_HEIGHT = 6
    
    area_names = sorted(df_area['titulo'].unique())
    area_colors = sns.color_palette('viridis_r', n_colors=len(area_names))
    AREA_COLOR_MAP = dict(zip(area_names, area_colors))

    # --- 3. FUNÇÕES AUXILIARES DE PLOTAGEM ---

    def _apply_common_style(ax, title, is_vertical=False):
        ax.set_title(title, fontsize=18, weight='bold', pad=15)
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(length=0)
        ax.grid(axis='y' if not is_vertical else 'x', visible=False)
        ax.grid(axis='x' if not is_vertical else 'y', color='#e0e0e0', linestyle='--', linewidth=0.7)

    def _add_smart_labels_single_bar(ax):
        threshold_ratio = 0.08
        for bar in ax.patches:
            width = bar.get_width()
            if width == 0: continue
            threshold = ax.get_xlim()[1] * threshold_ratio
            if width < threshold:
                ax.text(width + ax.get_xlim()[1] * 0.01, bar.get_y() + bar.get_height() / 2,
                        f'{int(width)}', ha='left', va='center', color='black', fontsize=9)
            else:
                ax.text(width / 2, bar.get_y() + bar.get_height() / 2, f'{int(width)}',
                        ha='center', va='center', color='white', weight='bold', fontsize=10)

    def _add_labels_to_stacked_bar(ax, bars):
        for bar in bars:
            width = bar.get_width()
            if width > ax.get_xlim()[1] * 0.04:
                ax.text(bar.get_x() + width / 2, bar.get_y() + bar.get_height() / 2,
                        f'{int(width)}', ha='center', va='center',
                        color='white', fontsize=10, weight='bold')

    # --- 4. GERAÇÃO DOS GRÁFICOS ---

    # Gráfico 1: Alunos por Área
    df_plot = df_area.sort_values('matriculados', ascending=False)
    chart_height = max(MIN_CHART_HEIGHT, len(df_plot) * INCH_PER_BAR)
    fig, ax = plt.subplots(figsize=(12, chart_height))
    sns.barplot(data=df_plot, x='matriculados', y='titulo', palette=AREA_COLOR_MAP, 
                hue='titulo', legend=False, ax=ax)
    _apply_common_style(ax, 'Demanda: Total de Alunos por Área (Câmara)')
    ax.set_xlabel('Número Total de Matrículas', fontsize=12)
    ax.set_ylabel('Área (Câmara)', fontsize=12)
    _add_smart_labels_single_bar(ax)
    plt.tight_layout(pad=1.0)
    plt.show()

    # Gráfico 2: Alunos por Componente
    df_plot = df_component[df_component['matriculados'] > 0].sort_values('matriculados', ascending=False)
    chart_height = max(MIN_CHART_HEIGHT, len(df_plot) * INCH_PER_BAR * 0.6)
    fig, ax = plt.subplots(figsize=(12, chart_height))
    sns.barplot(data=df_plot, x='matriculados', y='titulo', palette=SINGLE_VALUE_PALETTE, 
                hue='titulo', legend=False, ax=ax)
    _apply_common_style(ax, 'Demanda: Total de Alunos por Componente')
    ax.set_xlabel('Número de Matrículas', fontsize=12)
    ax.set_ylabel('Componente Curricular', fontsize=12)
    ax.tick_params(axis='y', labelsize=10)
    _add_smart_labels_single_bar(ax)
    plt.tight_layout(pad=1.0)
    plt.show()

    # Gráfico 3 & 4: Carga Horária
    df_plot = df_area.sort_values('ch_total', ascending=False)
    chart_height = max(MIN_CHART_HEIGHT, len(df_plot) * INCH_PER_BAR)
    fig, ax = plt.subplots(figsize=(14, chart_height))
    b1 = ax.barh(df_plot['titulo'], df_plot['ch_teorica'], label='Carga Horária Teórica', color=THEORY_COLOR, height=0.8)
    b2 = ax.barh(df_plot['titulo'], df_plot['ch_pratica'], left=df_plot['ch_teorica'], label='Carga Horária Prática', color=PRACTICE_COLOR, height=0.8)
    _apply_common_style(ax, 'Demanda: Carga Horária Total por Área (Câmara)')
    ax.invert_yaxis()
    ax.legend()
    _add_labels_to_stacked_bar(ax, b1)
    _add_labels_to_stacked_bar(ax, b2)
    plt.tight_layout(pad=1.0)
    plt.show()

    df_plot = df_component[df_component['ch_total'] > 0].sort_values('ch_total', ascending=False)
    chart_height = max(MIN_CHART_HEIGHT, len(df_plot) * INCH_PER_BAR * 0.6)
    fig, ax = plt.subplots(figsize=(14, chart_height))
    b1c = ax.barh(df_plot['titulo'], df_plot['ch_teorica'], label='Carga Horária Teórica', color=THEORY_COLOR, height=0.8)
    b2c = ax.barh(df_plot['titulo'], df_plot['ch_pratica'], left=df_plot['ch_teorica'], label='Carga Horária Prática', color=PRACTICE_COLOR, height=0.8)
    _apply_common_style(ax, 'Demanda: Carga Horária Total por Componente')
    ax.tick_params(axis='y', labelsize=10)
    ax.invert_yaxis()
    ax.legend()
    _add_labels_to_stacked_bar(ax, b1c)
    _add_labels_to_stacked_bar(ax, b2c)
    plt.tight_layout(pad=1.0)
    plt.show()

    # Gráfico 5: Fatores de Proporção
    indicators = {
        'ch_total': 'Carga Horária', 'matriculados': 'Matrículas',
        'prop_forca_trabalho': 'Força de Trabalho', 'pre_requisito': 'Pré-Requisitos',
        'obrigatorio_generalista': 'Obrigatórias'
    }
    df_norm = df_area[['titulo'] + list(indicators.keys())].copy()
    for col, new_name in indicators.items():
        total = df_norm[col].sum()
        df_norm[new_name] = (df_norm[col] / total) * 100 if total > 0 else 0
    df_melted = df_norm.drop(columns=list(indicators.keys())).melt(id_vars='titulo', var_name='Indicador', value_name='Proporção (%)')
    
    order = df_area.sort_values('matriculados', ascending=False)['titulo']
    fig, ax = plt.subplots(figsize=(16, 9)) # Tamanho reduzido
    sns.barplot(data=df_melted, x='titulo', y='Proporção (%)', hue='Indicador', 
                order=order, palette='Set2', ax=ax)
    _apply_common_style(ax, 'Demanda: Análise Comparativa dos Fatores por Área', is_vertical=True)
    ax.set_ylabel('Proporção Percentual (%)', fontsize=12)
    ax.set_xlabel('Área (Câmara)', fontsize=12)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=11)
    ax.legend(title='Indicador', fontsize=11, title_fontsize=13)
    plt.tight_layout(pad=1.0)
    plt.show()

    # Gráfico 6 & 7: Bolsas
    df_plot = df_area.sort_values('bolsas_total', ascending=False)
    chart_height = max(MIN_CHART_HEIGHT, len(df_plot) * INCH_PER_BAR)
    fig, ax = plt.subplots(figsize=(14, chart_height))
    b1b = ax.barh(df_plot['titulo'], df_plot['bolsas_teorica'], label='Bolsas Teóricas', color=THEORY_COLOR, height=0.8)
    b2b = ax.barh(df_plot['titulo'], df_plot['bolsas_pratica'], left=df_plot['bolsas_teorica'], label='Bolsas Práticas', color=PRACTICE_COLOR, height=0.8)
    _apply_common_style(ax, 'Resultado: Composição das Bolsas por Área')
    ax.invert_yaxis()
    ax.legend()
    _add_labels_to_stacked_bar(ax, b1b)
    _add_labels_to_stacked_bar(ax, b2b)
    plt.tight_layout(pad=1.0)
    plt.show()

    df_plot = df_component[df_component['bolsas_total'] > 0].sort_values('bolsas_total', ascending=False)
    chart_height = max(MIN_CHART_HEIGHT, len(df_plot) * INCH_PER_BAR * 0.6)
    fig, ax = plt.subplots(figsize=(14, chart_height))
    b1cb = ax.barh(df_plot['titulo'], df_plot['bolsas_teorica'], label='Bolsas Teóricas', color=THEORY_COLOR, height=0.8)
    b2cb = ax.barh(df_plot['titulo'], df_plot['bolsas_pratica'], left=df_plot['bolsas_teorica'], label='Bolsas Práticas', color=PRACTICE_COLOR, height=0.8)
    _apply_common_style(ax, 'Resultado: Composição das Bolsas por Componente')
    ax.tick_params(axis='y', labelsize=10)
    ax.invert_yaxis()
    ax.legend()
    _add_labels_to_stacked_bar(ax, b1cb)
    _add_labels_to_stacked_bar(ax, b2cb)
    plt.tight_layout(pad=1.0)
    plt.show()

    # Gráfico 8: Resumo Final
    df_plot = df_area.sort_values('bolsas_total', ascending=False)
    chart_height = max(MIN_CHART_HEIGHT, len(df_plot) * INCH_PER_BAR)
    fig, ax = plt.subplots(figsize=(12, chart_height))
    sns.barplot(data=df_plot, x='bolsas_total', y='titulo', palette=AREA_COLOR_MAP,
                hue='titulo', legend=False, ax=ax)
    _apply_common_style(ax, 'Resultado Final: Total de Bolsas por Área')
    ax.set_xlabel('Número Total de Bolsas', fontsize=12)
    ax.set_ylabel('Área (Câmara)', fontsize=12)
    _add_smart_labels_single_bar(ax)
    plt.tight_layout(pad=1.0)
    plt.show()