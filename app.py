
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

# Load analytics files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

daily = pd.read_parquet(os.path.join(DATA_DIR, "daily_metrics.parquet"))
products = pd.read_parquet(os.path.join(DATA_DIR, "product_metrics.parquet"))
reviews = pd.read_parquet(os.path.join(DATA_DIR, "review_sample.parquet"))
monthly = pd.read_parquet(os.path.join(DATA_DIR, "monthly_metrics.parquet"))
monthly_rating = pd.read_parquet(os.path.join(DATA_DIR, "monthly_rating_metrics.parquet"))
complaints = pd.read_parquet(os.path.join(DATA_DIR, "top_complaints.parquet"))

with open(os.path.join(DATA_DIR, "executive_metrics.json")) as f:
    metrics = json.load(f)

with open(os.path.join(DATA_DIR, "ml_metrics.json")) as f:
    ml_metrics = json.load(f)

# Prepare dates and searchable columns
daily["review_date"] = pd.to_datetime(daily["review_date"])
reviews["timestamp"] = pd.to_datetime(reviews["timestamp"], errors="coerce")
reviews["parent_asin"] = reviews["parent_asin"].astype(str)

# Initialize Dash
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True
)

app.title = "ReviewSense | Executive Intelligence"

# Reusable KPI card
def kpi_card(title, value, color):
    return dbc.Card(
        dbc.CardBody([
            html.P(title, className="text-secondary mb-2"),
            html.H3(value, className="fw-bold", style={"color": color})
        ]),
        className="shadow-sm h-100",
        style={"borderRadius": "14px", "backgroundColor": "#202938"}
    )

# Layout
app.layout = dbc.Container([

    # Header
    dbc.Row([
        dbc.Col([
            html.H2(
                "ReviewSense",
                className="fw-bold mb-1",
                style={"color": "#63D6C5"}
            ),
            html.P(
                "EXECUTIVE INTELLIGENCE | E-COMMERCE REVIEW ANALYTICS",
                className="text-secondary"
            )
        ], width=9),
        dbc.Col([
            html.H6(
                "LIVE ANALYTICS",
                className="text-success text-end"
            )
        ], width=3)
    ], className="pt-4 pb-3"),

    # Filters
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Sentiment"),
                    dcc.Dropdown(
                        id="sentiment-filter",
                        options=[
                            {"label": "All", "value": "all"},
                            {"label": "Positive", "value": "positive"},
                            {"label": "Negative", "value": "negative"},
                            {"label": "Neutral", "value": "neutral"}
                        ],
                        value="all",
                        clearable=False
                    )
                ], md=4),
                dbc.Col([
                    html.Label("Verified Purchase"),
                    dcc.Dropdown(
                        id="verified-filter",
                        options=[
                            {"label": "All", "value": "all"},
                            {"label": "Verified", "value": "true"},
                            {"label": "Not Verified", "value": "false"}
                        ],
                        value="all",
                        clearable=False
                    )
                ], md=4),
                dbc.Col([
                    html.Label("Date Range"),
                    dcc.DatePickerRange(
                        id="date-filter",
                        min_date_allowed=daily["review_date"].min(),
                        max_date_allowed=daily["review_date"].max(),
                        start_date=daily["review_date"].min(),
                        end_date=daily["review_date"].max(),
                        display_format="DD MMM YYYY",
                        style={"backgroundColor": "white"}
                    )
                ], md=4)
            ])
        ]),
        className="mb-4 shadow-sm"
    ),

    # KPI cards
    dbc.Row([
        dbc.Col(html.Div(id="kpi-total"), md=3),
        dbc.Col(html.Div(id="kpi-positive"), md=3),
        dbc.Col(html.Div(id="kpi-negative"), md=3),
        dbc.Col(html.Div(id="kpi-rating"), md=3)
    ], className="g-3 mb-4"),

    # Sentiment charts
    dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H5("Customer Sentiment Distribution"),
                dcc.Graph(id="sentiment-chart")
            ])),
            md=5
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H5("Monthly Review Trend"),
                dcc.Graph(id="monthly-chart")
            ])),
            md=7
        )
    ], className="g-3 mb-4"),

    # Year-wise customer review trend
    dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H5("Year-wise Customer Review Trend"),
                dcc.Graph(id="yearly-chart")
            ])),
            md=12
        )
    ], className="g-3 mb-4"),

    # Product charts
    dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H5("Top Products by Review Volume"),
                dcc.Graph(id="product-chart")
            ])),
            md=7
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H5("Customer Complaint Patterns"),
                dcc.Graph(id="complaint-chart")
            ])),
            md=5
        )
    ], className="g-3 mb-4"),

    # Product attention table
    dbc.Card(dbc.CardBody([
        html.H5("Products Requiring Attention"),
        html.P(
            "Products with at least 100 reviews and 15% or more negative reviews.",
            className="text-secondary"
        ),
        dash_table.DataTable(
            id="attention-table",
            columns=[
                {"name": "Product ID", "id": "parent_asin"},
                {"name": "Total Reviews", "id": "total_reviews"},
                {"name": "Average Rating", "id": "average_rating"},
                {"name": "Negative Reviews %", "id": "negative_percentage"},
                {"name": "Attention Level", "id": "attention_level"}
            ],
            page_size=10,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#263445",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "backgroundColor": "#202938",
                "color": "white",
                "padding": "10px",
                "textAlign": "left"
            },
            style_data_conditional=[
                {
                    "if": {"filter_query": '{attention_level} = "High"'},
                    "color": "#ff7675"
                },
                {
                    "if": {"filter_query": '{attention_level} = "Medium"'},
                    "color": "#ffd166"
                }
            ]
        )
    ]), className="mb-4"),

    # Review explorer
    dbc.Card(dbc.CardBody([
        html.H5("Customer Review Explorer"),
        dbc.Row([
            dbc.Col([
                dcc.Input(
                    id="product-search",
                    placeholder="Search Product ID...",
                    type="text",
                    className="form-control"
                )
            ], md=6),
            dbc.Col([
                dbc.Button(
                    "Download Filtered Reviews",
                    id="download-button",
                    color="info",
                    className="w-100"
                ),
                dcc.Download(id="download-reviews")
            ], md=6)
        ], className="mb-3"),
        dash_table.DataTable(
            id="review-table",
            columns=[
                {"name": "Product ID", "id": "parent_asin"},
                {"name": "Rating", "id": "rating"},
                {"name": "Sentiment", "id": "sentiment"},
                {"name": "Review", "id": "text"},
                {"name": "Verified", "id": "verified_purchase"}
            ],
            page_size=10,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#263445",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "backgroundColor": "#202938",
                "color": "white",
                "padding": "10px",
                "textAlign": "left",
                "whiteSpace": "normal",
                "height": "auto",
                "minWidth": "100px",
                "maxWidth": "350px"
            }
        )
    ]), className="mb-4"),

    # Machine learning section
    dbc.Card(dbc.CardBody([
        html.H5("Machine Learning Model Performance"),
        html.H2(
            f"{ml_metrics['accuracy_percentage']:.2f}%",
            style={"color": "#63D6C5"}
        ),
        html.P("TF-IDF + Logistic Regression Accuracy"),
        dbc.Progress(
            value=ml_metrics["accuracy_percentage"],
            color="info",
            className="mb-2",
            style={"height": "12px"}
        ),
        html.P(
            "Evaluation performed on a balanced held-out test set.",
            className="text-secondary"
        )
    ]), className="mb-4"),

    html.P(
        "ReviewSense | E-Commerce Product Review and Sentiment Analytics",
        className="text-center text-secondary pb-4"
    )

], fluid=True, style={"maxWidth": "1500px"})


# Main dashboard callback
@app.callback(
    [
        Output("kpi-total", "children"),
        Output("kpi-positive", "children"),
        Output("kpi-negative", "children"),
        Output("kpi-rating", "children"),
        Output("sentiment-chart", "figure"),
        Output("monthly-chart", "figure"),
        Output("yearly-chart", "figure"),
        Output("product-chart", "figure"),
        Output("complaint-chart", "figure"),
        Output("attention-table", "data")
    ],
    [
        Input("sentiment-filter", "value"),
        Input("verified-filter", "value"),
        Input("date-filter", "start_date"),
        Input("date-filter", "end_date")
    ]
)
def update_dashboard(sentiment, verified, start_date, end_date):

    # Filter daily analytics
    filtered = daily.copy()

    if sentiment != "all":
        filtered = filtered[filtered["sentiment"] == sentiment]

    if verified != "all":
        verified_value = verified == "true"
        filtered = filtered[
            filtered["verified_purchase"] == verified_value
        ]

    if start_date:
        filtered = filtered[
            filtered["review_date"] >= pd.to_datetime(start_date)
        ]

    if end_date:
        filtered = filtered[
            filtered["review_date"] <= pd.to_datetime(end_date)
        ]

    # Calculate filtered KPIs
    total = int(filtered["review_count"].sum())

    positive = int(
        filtered.loc[
            filtered["sentiment"] == "positive",
            "review_count"
        ].sum()
    )

    negative = int(
        filtered.loc[
            filtered["sentiment"] == "negative",
            "review_count"
        ].sum()
    )

    rating_total = float(
        (filtered["rating"] * filtered["review_count"]).sum()
    )

    average = rating_total / total if total else 0

    # Sentiment distribution
    sentiment_data = (
        filtered.groupby("sentiment")["review_count"]
        .sum()
        .reset_index()
    )

    sentiment_fig = px.pie(
        sentiment_data,
        names="sentiment",
        values="review_count",
        hole=0.55,
        template="plotly_dark"
    )

    # Monthly trend
    monthly_filtered = filtered.copy()
    monthly_filtered["year_month"] = (
        monthly_filtered["review_date"].dt.to_period("M").astype(str)
    )

    monthly_data = (
        monthly_filtered.groupby(
            ["year_month", "sentiment"]
        )["review_count"]
        .sum()
        .reset_index()
    )

    monthly_fig = px.line(
        monthly_data,
        x="year_month",
        y="review_count",
        color="sentiment",
        markers=True,
        template="plotly_dark"
    )

    monthly_fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Reviews"
    )

    # Year-wise customer review trend
    yearly_data = filtered.copy()

    yearly_data["year"] = yearly_data["review_date"].dt.year

    yearly_data = (
        yearly_data.groupby("year")["review_count"]
        .sum()
        .reset_index()
        .sort_values("year")
    )

    yearly_fig = px.line(
        yearly_data,
        x="year",
        y="review_count",
        markers=True,
        template="plotly_dark",
        title="Annual Customer Review Volume"
    )

    yearly_fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Customer Reviews",
        xaxis=dict(dtick=1)
    )

    # Top products: product ranking uses full-dataset metrics
    top_products = products.head(10).sort_values(
        "total_reviews",
        ascending=True
    )

    product_fig = px.bar(
        top_products,
        x="total_reviews",
        y="parent_asin",
        orientation="h",
        color="average_rating",
        template="plotly_dark",
        title="Top 10 Products"
    )

    # Complaint patterns: full negative-review sample
    complaint_fig = px.bar(
        complaints.head(10).sort_values("frequency"),
        x="frequency",
        y="complaint_phrase",
        orientation="h",
        template="plotly_dark"
    )

    # Attention table: full-dataset attention ranking
    attention_data = (
        products[products["requires_attention"]]
        .sort_values(
            "negative_percentage",
            ascending=False
        )
        [[
            "parent_asin",
            "total_reviews",
            "average_rating",
            "negative_percentage",
            "attention_level"
        ]]
        .head(100)
        .to_dict("records")
    )

    # Return updated dashboard components
    return (
        kpi_card("Filtered Reviews", f"{total:,}", "#63D6C5"),
        kpi_card("Positive Reviews", f"{positive:,}", "#63D6C5"),
        kpi_card("Negative Reviews", f"{negative:,}", "#FF7675"),
        kpi_card("Average Rating", f"{average:.2f}/5", "#FFD166"),
        sentiment_fig,
        monthly_fig,
        yearly_fig,
        product_fig,
        complaint_fig,
        attention_data
    )


# Review explorer callback
@app.callback(
    Output("review-table", "data"),
    [
        Input("product-search", "value"),
        Input("sentiment-filter", "value"),
        Input("verified-filter", "value")
    ]
)
def update_reviews(search, sentiment, verified):

    filtered_reviews = reviews.copy()

    if search:
        filtered_reviews = filtered_reviews[
            filtered_reviews["parent_asin"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    if sentiment != "all":
        filtered_reviews = filtered_reviews[
            filtered_reviews["sentiment"] == sentiment
        ]

    if verified != "all":
        verified_value = verified == "true"
        filtered_reviews = filtered_reviews[
            filtered_reviews["verified_purchase"] == verified_value
        ]

    return filtered_reviews[
        [
            "parent_asin",
            "rating",
            "sentiment",
            "text",
            "verified_purchase"
        ]
    ].head(500).fillna("").to_dict("records")


# Review download callback
@app.callback(
    Output("download-reviews", "data"),
    Input("download-button", "n_clicks"),
    [
        State("product-search", "value"),
        State("sentiment-filter", "value"),
        State("verified-filter", "value")
    ],
    prevent_initial_call=True
)
def download_reviews(n_clicks, search, sentiment, verified):

    filtered_reviews = reviews.copy()

    if search:
        filtered_reviews = filtered_reviews[
            filtered_reviews["parent_asin"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    if sentiment != "all":
        filtered_reviews = filtered_reviews[
            filtered_reviews["sentiment"] == sentiment
        ]

    if verified != "all":
        verified_value = verified == "true"
        filtered_reviews = filtered_reviews[
            filtered_reviews["verified_purchase"] == verified_value
        ]

    export_data = filtered_reviews[
        [
            "parent_asin",
            "rating",
            "sentiment",
            "text",
            "verified_purchase"
        ]
    ]

    return dcc.send_data_frame(
        export_data.to_csv,
        "reviewsense_filtered_reviews.csv",
        index=False
    )


# Run application
server = app.server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
