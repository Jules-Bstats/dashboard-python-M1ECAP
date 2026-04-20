
# ─── Import ───────────────────────────────────────────────
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc

# ─── CHARTE GRAPHIQUE ───────────────────────────────────────────────
COLORS = {
    "bg":       "#1A1A2E",
    "accent":   "#E94560",
    "teal":     "#0FC3C3",
    "gold":     "#F5A623",
    "purple":   "#8B5CF6",
    "light":    "#F4F4F8",
    "muted":    "#8A8A9A",
    "white":    "#FFFFFF",
    "paper":    "#FFFFFF",
    "plot_bg":  "#F9F9FC",
}

# Mapping genre → couleur (Female = accent, Male = teal)
GENDER_COLORS = {"Female": COLORS["accent"], "Male": COLORS["teal"]}

# Mapping ville → couleur
CITY_COLORS = {
    "Mandalay":  COLORS["gold"],
    "Naypyitaw": COLORS["purple"],
    "Yangon":    COLORS["bg"],
}

# Palette pour le camembert (6 catégories)
PIE_COLORS = ["#E94560", "#0FC3C3", "#F5A623", "#8B5CF6", "#3DD68C", "#F87171"]

# Template Plotly unifié
CHART_LAYOUT = dict(
    font=dict(family="DM Sans, sans-serif", color="#1A1A2E", size=12),
    paper_bgcolor=COLORS["paper"],
    plot_bgcolor=COLORS["plot_bg"],
    margin=dict(t=40, b=40, l=50, r=20),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="right",  x=1,
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.05)",
        linecolor="rgba(0,0,0,0.1)",
        tickfont=dict(size=11),
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.05)",
        linecolor="rgba(0,0,0,0.1)",
        tickfont=dict(size=11),
    ),
)

# ─── DONNÉES ────────────────────────────────────────────────────────
data = pd.read_csv("data/supermarket_sales.csv")
data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
data["Week"] = data["Date"].dt.to_period("W").apply(lambda r: r.start_time)

CITIES   = sorted(data["City"].unique())
GENDERS  = sorted(data["Gender"].unique())

# ─── FONCTIONS DATA ─────────────────────────────────────────────────
def filter_data(cities, genders):
    df = data.copy()
    if cities:
        df = df[df["City"].isin(cities if isinstance(cities, list) else [cities])]
    if genders:
        df = df[df["Gender"].isin(genders if isinstance(genders, list) else [genders])]
    return df


def kpi_values(df, gender, city):
    """Retourne (valeur_choisie, valeur_reference) pour nb achats et montant."""
    other_gender = [g for g in GENDERS if g != gender][0]
    sel = df[(df["Gender"] == gender) & (df["City"] == city)]
    ref = df[(df["Gender"] == other_gender) & (df["City"] == city)]

    nb_val  = len(sel)
    nb_ref  = len(ref)
    amt_val = sel["Total"].sum()
    amt_ref = ref["Total"].sum()
    return nb_val, nb_ref, amt_val, amt_ref


# ─── FIGURES ────────────────────────────────────────────────────────
def make_indicator_fig(df, gender, city):
    nb_val, nb_ref, amt_val, amt_ref = kpi_values(df, gender, city)

    fig = go.Figure()

    # Indicateur : Nombre d'achats
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=nb_val,
        delta=dict(
            reference=nb_ref, 
            increasing=dict(color=COLORS["teal"]),
            decreasing=dict(color=COLORS["accent"]),
            font=dict(size=16) # Delta plus lisible
        ),
        title=dict(
            text=f"Nombre d'achats<br><span style='color:{COLORS['muted']}'>{gender} · {city}</span>",
            font=dict(size=15, color=COLORS["white"]) # Titre agrandi
        ),
        number=dict(
            font=dict(size=42, family="Syne, sans-serif", color=COLORS["white"]) # Chiffre boosté à 42
        ),
        domain=dict(x=[0, 0.45], y=[0, 1]),
    ))

    # Indicateur : Montant total
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=amt_val,
        delta=dict(
            reference=amt_ref, 
            increasing=dict(color=COLORS["teal"]),
            decreasing=dict(color=COLORS["accent"]),
            valueformat=",.0f",
            font=dict(size=16) 
        ),
        title=dict(
            text=f"Montant total ($)<br><span style='color:{COLORS['muted']}'>{gender} · {city}</span>",
            font=dict(size=15, color=COLORS["white"]) # Titre agrandi
        ),
        number=dict(
            font=dict(size=42, family="Syne, sans-serif", color=COLORS["white"]), # Chiffre boosté à 42
            valueformat=",.0f"
        ),
        domain=dict(x=[0.55, 1], y=[0, 1]),
    ))

    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        # Marges réduites au strict minimum pour laisser la place au texte
        margin=dict(t=30, b=0, l=10, r=10),
        height=180, # Augmenté légèrement pour éviter le chevauchement
        font=dict(family="DM Sans, sans-serif"),
    )
    
    return fig

def make_bar_fig(df):
    grp = (df.groupby(["City", "Gender"])
             .size()
             .reset_index(name="Nombre_total_achat"))

    fig = px.bar(
        grp, x="City", y="Nombre_total_achat", color="Gender",
        barmode="group",
        color_discrete_map=GENDER_COLORS,
        labels={"Nombre_total_achat": "Nombre d'achats", "City": "Ville"},
    )

    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Nombre total d'achats", font=dict(family="Syne, sans-serif", size=14, color=COLORS["bg"]), x=0.02),
        height=300,
    )
    return fig


def make_histogram_fig(df):
    grp = (df.groupby(["City", "Gender"])["Total"]
             .sum()
             .reset_index())

    fig = px.bar(
        grp, x="City", y="Total", color="Gender",
        barmode="group",
        color_discrete_map=GENDER_COLORS,
        labels={"Total": "Montant total ($)", "City": "Ville"},
    )

    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Montant total des achats", font=dict(family="Syne, sans-serif", size=14, color=COLORS["bg"]), x=0.02),
        height=300,
    )
    return fig


def make_pie_fig(df):
    grp = (df.groupby("Product line")
             .size()
             .reset_index(name="Nombre_commande"))

    fig = px.pie(
        grp, values="Nombre_commande", names="Product line",
        color_discrete_sequence=PIE_COLORS,
        hole=0.42,
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(family="DM Sans, sans-serif", size=11),
        marker=dict(line=dict(color=COLORS["white"], width=2)),
    )
    fig.update_layout(
        paper_bgcolor=COLORS["paper"],
        margin=dict(t=50, b=20, l=20, r=20),
        title=dict(text="Répartition par catégorie de produit", font=dict(family="Syne, sans-serif", size=14, color=COLORS["bg"]), x=0.02),
        legend=dict(font=dict(size=10), orientation="v"),
        height=340,
    )
    return fig


def make_weekly_fig(df):
    grp = (df.groupby(["Week", "City"])["Total"]
             .sum()
             .reset_index())

    fig = px.line(
        grp, x="Week", y="Total", color="City",
        color_discrete_map=CITY_COLORS,
        markers=True,
        labels={"Total": "Montant ($)", "Week": "Semaine"},
    )

    fig.update_traces(line=dict(width=2.5), marker=dict(size=5))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Évolution hebdomadaire par ville", font=dict(family="Syne, sans-serif", size=14, color=COLORS["bg"]), x=0.02),
        height=300,
    )
    return fig


# ─── LAYOUT ─────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="SuperMega Market",
)

app.layout = html.Div([

    # ── HEADER ──
    html.Div(className="smm-header", children=[
        html.Div([
            html.Div([
                html.Span("Super", className="accent"),
                "Mega Market",
            ], className="smm-logo",
            style={
            "fontSize": "40px",          # Taille augmentée (ajuste selon tes besoins)
            "fontWeight": "800",         # Plus gras pour l'impact
            "letterSpacing": "-1.5px",   # Look moderne un peu serré
            "lineHeight": "1"            # Évite les décalages verticaux
        }),
        ]),
        html.Div("🛒", style={"fontSize": "24px", "opacity": "0.6"}),
    ]),

    # ── FILTRES ──
    html.Div(className="smm-filters-bar", children=[
        html.Span("Filtres :", className="smm-filter-label"),
        dcc.Dropdown(
            id="filter-city",
            options=[{"label": c, "value": c} for c in CITIES],
            value=None,
            multi=True,
            placeholder="Toutes les villes",
            style={"width": "420px", "fontSize": "13px"},
            clearable=True,
        ),
        dcc.Dropdown(
            id="filter-gender",
            options=[{"label": g, "value": g} for g in GENDERS],
            value=None,
            multi=False,
            placeholder="Tous les genres",
            style={"width": "420px", "fontSize": "13px"},
            clearable=True,
        )
    ]),

    # ── MAIN ──
    html.Div(className="smm-main", children=[

        # ── LIGNE 1 : KPI ──
        dbc.Row([
            dbc.Col(
                html.Div(className="smm-kpi-card", children=[
                    dcc.Graph(id="kpi-graph", className="smm-kpi-graph",
                              config={"displayModeBar": False}),
                ]),
                width=12
            ),
        ], className="mb-3"),

        # ── LIGNE 2 : barres ──
        
        dbc.Row([
            dbc.Col(
                html.Div(className="smm-chart-card",
                         children=[dcc.Graph(id="bar-graph", config={"displayModeBar": False})]),
                md=6
            ),
            dbc.Col(
                html.Div(className="smm-chart-card",
                         children=[dcc.Graph(id="hist-graph", config={"displayModeBar": False})]),
                md=6
            ),
        ], className="mb-3"),

        # ── LIGNE 3 : camembert + tendance ──
        dbc.Row([
            dbc.Col(
                html.Div(className="smm-chart-card",
                         children=[dcc.Graph(id="pie-graph", config={"displayModeBar": False})]),
                md=5
            ),
            dbc.Col(
                html.Div(className="smm-chart-card",
                         children=[dcc.Graph(id="weekly-graph", config={"displayModeBar": False})]),
                md=7
            ),
        ]),
    ]),
])


# ─── CALLBACKS ──────────────────────────────────────────────────────
@callback(
    Output("kpi-graph",    "figure"),
    Output("bar-graph",    "figure"),
    Output("hist-graph",   "figure"),
    Output("pie-graph",    "figure"),
    Output("weekly-graph", "figure"),
    Input("filter-city",   "value"),
    Input("filter-gender", "value"),
)
def update_all(cities, gender):
    df = filter_data(cities, gender)

    # Valeurs par défaut pour l'indicateur
    city_for_kpi   = (cities[0] if isinstance(cities, list) and cities else
                      cities   if isinstance(cities, str) else CITIES[0])
    gender_for_kpi = gender if gender else GENDERS[0]

    # Si le df filtré est vide, on retourne des figures vides
    if df.empty:
        empty = go.Figure()
        empty.update_layout(paper_bgcolor=COLORS["paper"],
                            annotations=[dict(text="Aucune donnée", showarrow=False,
                                              font=dict(size=14, color=COLORS["muted"]))])
        return empty, empty, empty, empty, empty

    return (
        make_indicator_fig(df, gender_for_kpi, city_for_kpi),
        make_bar_fig(df),
        make_histogram_fig(df),
        make_pie_fig(df),
        make_weekly_fig(df),
    )


if __name__ == "__main__":
    app.run(debug=True, port=8060)
