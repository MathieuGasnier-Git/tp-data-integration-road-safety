import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

GOLD_DIR = Path("data/gold")

SEVERITY_COLORS = {
    "Fatal": "#E63946",
    "Severe": "#F77F00",
    "Minor": "#FCBF49",
    "No injury": "#2A9D8F",
}

st.set_page_config(page_title="French Road Safety Dashboard", page_icon="🚗", layout="wide")

st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }
    .kpi-card {
        background-color: #161B22;
        border: 1px solid #262B33;
        border-left: 5px solid #FF4B4B;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #FAFAFA;
    }
    .kpi-label {
        font-size: 14px;
        color: #9AA0A6;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .hero {
        background: linear-gradient(90deg, #7A1F2B 0%, #161B22 100%);
        padding: 28px 32px;
        border-radius: 14px;
        margin-bottom: 24px;
    }
    .hero h1 {
        margin: 0;
        color: #FAFAFA;
    }
    .hero p {
        margin: 6px 0 0 0;
        color: #D6D6D6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    fact_accidents = pd.read_csv(GOLD_DIR / "fact_accidents.csv", parse_dates=["accident_date"])
    fact_vehicles = pd.read_csv(GOLD_DIR / "fact_vehicles.csv")
    fact_users = pd.read_csv(GOLD_DIR / "fact_users.csv")
    dim_location = pd.read_csv(GOLD_DIR / "dim_location.csv", dtype={"dep": str})
    return fact_accidents, fact_vehicles, fact_users, dim_location


def kpi_card(column, label, value):
    column.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


fact_accidents, fact_vehicles, fact_users, dim_location = load_data()

fact_accidents["dep"] = fact_accidents["dep"].astype(str)
fact_accidents = fact_accidents.merge(dim_location, on="dep", how="left")
fact_accidents["month_name"] = fact_accidents["accident_date"].dt.month_name()

st.markdown(
    """
    <div class="hero">
        <h1>French Road Safety Dashboard</h1>
        <p>Gold layer analytical model built from the 2024 French road safety open data (accidents corporels).</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Filters")

departments = sorted(fact_accidents["dep_name"].dropna().unique())
selected_departments = st.sidebar.multiselect("Department", departments)

severities = sorted(fact_accidents["severity_category"].dropna().unique())
selected_severities = st.sidebar.multiselect("Severity category", severities)

times_of_day = sorted(fact_accidents["time_of_day"].dropna().unique())
selected_times = st.sidebar.multiselect("Time of day", times_of_day)

filtered = fact_accidents.copy()
if selected_departments:
    filtered = filtered[filtered["dep_name"].isin(selected_departments)]
if selected_severities:
    filtered = filtered[filtered["severity_category"].isin(selected_severities)]
if selected_times:
    filtered = filtered[filtered["time_of_day"].isin(selected_times)]

col1, col2, col3, col4 = st.columns(4)
kpi_card(col1, "Accidents", f"{len(filtered):,}")
kpi_card(col2, "Killed", f"{int(filtered['nb_killed'].sum()):,}")
kpi_card(col3, "Hospitalized injured", f"{int(filtered['nb_hospitalized'].sum()):,}")
kpi_card(col4, "Vehicles involved", f"{int(filtered['nb_vehicles'].sum()):,}")

st.write("")

tab_map, tab_trends, tab_vehicles = st.tabs(["Map", "Trends", "Vehicles & Users"])

with tab_map:
    map_data = filtered.dropna(subset=["lat", "long"])
    if len(map_data) > 0:
        fig_map = px.scatter_mapbox(
            map_data,
            lat="lat",
            lon="long",
            color="severity_category",
            color_discrete_map=SEVERITY_COLORS,
            hover_data=["dep_name", "accident_date", "time_of_day"],
            zoom=4,
            height=600,
            mapbox_style="carto-darkmatter",
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text="Severity")
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No accidents with valid coordinates for the current filters.")

with tab_trends:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Accidents by month")
        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        monthly_counts = filtered["month_name"].value_counts().reindex(month_order).fillna(0)
        fig_month = px.bar(
            x=monthly_counts.index, y=monthly_counts.values,
            labels={"x": "Month", "y": "Accidents"}, template="plotly_dark",
            color_discrete_sequence=["#FF4B4B"],
        )
        st.plotly_chart(fig_month, use_container_width=True)

    with col_right:
        st.subheader("Accidents by time of day")
        time_counts = filtered["time_of_day"].value_counts()
        fig_time = px.bar(
            x=time_counts.index, y=time_counts.values,
            labels={"x": "Time of day", "y": "Accidents"}, template="plotly_dark",
            color_discrete_sequence=["#F77F00"],
        )
        st.plotly_chart(fig_time, use_container_width=True)

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Severity category distribution")
        severity_counts = filtered["severity_category"].value_counts()
        fig_severity = px.pie(
            names=severity_counts.index, values=severity_counts.values,
            color=severity_counts.index, color_discrete_map=SEVERITY_COLORS,
            hole=0.45, template="plotly_dark",
        )
        st.plotly_chart(fig_severity, use_container_width=True)

    with col_right2:
        st.subheader("Top 10 departments by accident count")
        top_departments = filtered["dep_name"].value_counts().head(10)
        fig_dep = px.bar(
            x=top_departments.values, y=top_departments.index, orientation="h",
            labels={"x": "Accidents", "y": "Department"}, template="plotly_dark",
            color_discrete_sequence=["#2A9D8F"],
        )
        fig_dep.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_dep, use_container_width=True)

with tab_vehicles:
    filtered_ids = filtered["Num_Acc"]
    vehicles_filtered = fact_vehicles[fact_vehicles["Num_Acc"].isin(filtered_ids)]
    users_filtered = fact_users[fact_users["Num_Acc"].isin(filtered_ids)]

    st.subheader("Vehicles involved by category")
    vehicle_counts = vehicles_filtered["catv_label"].value_counts().head(10)
    fig_vehicle = px.bar(
        x=vehicle_counts.values, y=vehicle_counts.index, orientation="h",
        labels={"x": "Vehicles", "y": "Vehicle category"}, template="plotly_dark",
        color_discrete_sequence=["#457B9D"],
    )
    fig_vehicle.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_vehicle, use_container_width=True)

    st.subheader("Users involved by category and severity")
    user_severity = users_filtered.groupby(["catu_label", "grav_label"]).size().reset_index(name="count")
    fig_users = px.bar(
        user_severity, x="catu_label", y="count", color="grav_label", barmode="group",
        labels={"catu_label": "User category", "count": "Users", "grav_label": "Severity"},
        template="plotly_dark",
        color_discrete_map={
            "Unharmed": "#2A9D8F", "Killed": "#E63946",
            "Hospitalized injured": "#F77F00", "Slightly injured": "#FCBF49",
        },
    )
    st.plotly_chart(fig_users, use_container_width=True)
