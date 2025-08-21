from shiny import App, ui, render
import pandas as pd
import json
#Importando o excel
try:
    df_anual = pd.read_excel("T01VEGAN_KEYWORDS_TBL_yyyy.xlsx")
    df_anual['created_at'] = pd.to_datetime(df_anual['created_at'], format="%Y")
except FileNotFoundError:
    print("ERRO: Arquivo 'T01VEGAN_KEYWORDS_TBL_yyyy.xlsx' não encontrado.")
    df_anual = None
except Exception as e:
    print(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
    df_anual = None

try:
    df_mensal_original = pd.read_excel("T01VEGAN_KEYWORDS_TBL_mm.xlsx")
    df_mensal_original['created_at'] = pd.to_datetime(df_mensal_original['created_at'])
except FileNotFoundError:
    print("ERRO: Arquivo 'T01VEGAN_KEYWORDS_TBL_mm.xlsx' não encontrado.")
    df_mensal_original = None
except Exception as e:
    print(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
    df_mensal_original = None

# --- Simulação de dados empilhados ---
df_anual_stacked = pd.DataFrame()
if df_anual is not None:
    df_anual_stacked['created_at'] = df_anual['created_at']
    df_anual_stacked['Posted'] = (df_anual['vegan'] * 0.40).astype(int)
    df_anual_stacked['Retweeted'] = (df_anual['vegan'] * 0.35).astype(int)
    df_anual_stacked['Replied'] = (df_anual['vegan'] * 0.25).astype(int)

df_mensal_stacked = pd.DataFrame()
if df_mensal_original is not None:
    df_mensal_stacked['created_at'] = df_mensal_original['created_at']
    df_mensal_stacked['Posted'] = (df_mensal_original['vegan'] * 0.40).astype(int)
    df_mensal_stacked['Retweeted'] = (df_mensal_original['vegan'] * 0.35).astype(int)
    df_mensal_stacked['Replied'] = (df_mensal_original['vegan'] * 0.25).astype(int)

metrics = ['Posted', 'Retweeted', 'Replied']
colors = ['#2f2f2f', '#696969', '#b2b2b2']

# --- UI corrigida ---
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_radio_buttons(
            "periodicidade",
            "Selecione a periodicidade:",
            {"Anual": "Anual", "Mensal": "Mensal"},
            selected="Anual"
        ),
        title="Controles",
        bg="#f8f8f8"
    ),
    ui.card(
        ui.output_ui("grafico_html"),
        ui.output_ui("grafico_script"),
        style="min-height: 500px;"
    ),
    ui.tags.head(
        ui.tags.script(src="https://code.highcharts.com/highcharts.js")
    ),
    title="Métricas em tweets"
)

# --- Server ---
def server(input, output, session):
    @render.ui
    def grafico_html():
        return ui.HTML('<div id="container" style="height: 400px; width: 100%;"></div>')

    @render.ui
    def grafico_script():
        periodicidade = input.periodicidade()

        if periodicidade == "Anual":
            df = df_anual_stacked
            if df.empty:
                return ui.tags.script("console.log('Dados anuais não disponíveis');")
            x_vals = df["created_at"].dt.year.astype(str).tolist()
            subtitle_text = "2012 a 2022"
        else:
            df = df_mensal_stacked
            if df.empty:
                return ui.tags.script("console.log('Dados mensais não disponíveis');")
            x_vals = df["created_at"].dt.strftime("%Y-%m").tolist()
            subtitle_text = "Dados Mensais"

        series_data = []
        for i, metric in enumerate(metrics):
            series_data.append({
                "name": metric,
                "data": df[metric].tolist() if metric in df.columns else [],
                "color": colors[i]
            })

        cfg = {
            "chart": {"type": "area"},
            "title": {"text": None},
            "subtitle": {"text": subtitle_text, "align": "left"},
            "xAxis": {"categories": x_vals, "tickmarkPlacement": "on", "title": {"enabled": False}},
            "yAxis": {
                "title": {"text": None},
                "labels": {
                    "format": "{value:,.0f}K"
                }
            },
            "tooltip": {
                "shared": True,
                "pointFormat": '<span style="color:{series.color}">●</span> {series.name}: <b>{point.y:,.0f}</b><br/>'
            },
            "plotOptions": {
                "area": {
                    "stacking": 'normal',
                    "lineColor": '#666666',
                    "lineWidth": 1,
                    "marker": {
                        "lineWidth": 1,
                        "lineColor": '#666666',
                        "symbol": "circle"
                    }
                }
            },
            "legend": {
                "layout": 'vertical',
                "align": 'left',
                "verticalAlign": 'top',
                "x": 80,
                "y": 40,
                "floating": True,
                "borderWidth": 1,
                "backgroundColor": '#FFFFFF',
                "title": {"text": "Métricas"}
            },
            "series": series_data,
            "credits": {"text": "Fonte: API do X/Twitter", "href": ""}
        }

        cfg_json = json.dumps(cfg)

        return ui.tags.script(
            f"""
            (function render() {{
                var go = (typeof Highcharts !== 'undefined') && document.getElementById('container');
                if (!go) {{ setTimeout(render, 50); return; }}
                Highcharts.chart('container', {cfg_json});
            }})();
            """
        )

app = App(app_ui, server)
