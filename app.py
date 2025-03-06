import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Load CSV File
df = pd.read_csv("networker_infrastructure.csv")

# Simulate Backup Success Rate (Random for Demo)
np.random.seed(42)
df["Backup Success Rate (%)"] = np.random.uniform(80, 100, size=len(df))

st.title("Networker Infrastructure Drilldown")

# Overall Backup Success Rate Pie Chart
st.subheader("Overall Backup Success vs Failure")
overall_success = df["Backup Success Rate (%)"].apply(lambda x: x if x >= 95 else 0).sum()
overall_failure = df["Backup Success Rate (%)"].apply(lambda x: 100 - x if x < 95 else 0).sum()

fig_overall = px.pie(
    names=["Success", "Failure"],
    values=[overall_success, overall_failure],
    title="Overall Backup Success Rate",
    color=["Success", "Failure"],
    color_discrete_map={"Success": "green", "Failure": "red"},
)

st.plotly_chart(fig_overall)

# Level 1: Location Selection
st.subheader("Step 1: Select Location")
locations = df["Location"].unique()
location = st.selectbox("Select Location", locations)

if location:
    location_df = df[df["Location"] == location]

    # Display NMC Server at Location
    nmc_server = location_df["NMC Server"].unique()[0]
    st.info(f"**NMC Server for {location}:** {nmc_server}")

    # Server Summary
    server_summary = location_df.groupby("Server").agg(
        Storage_Node_Count=("Storage Node", "nunique"),
        Client_Count=("Device", "nunique"),
        Backup_Success_Rate=("Backup Success Rate (%)", "mean")
    ).reset_index()

    # Round off and remove trailing zeros
    server_summary["Backup_Success_Rate"] = server_summary["Backup_Success_Rate"].round(2).apply(lambda x: f"{x:.2f}".rstrip('0').rstrip('.'))

    # Highlight Backup Success Rate in red if below 95%
    def highlight_rate(val):
        try:
            return f"color: {'red' if float(val) < 95 else 'green'}"
        except ValueError:
            return ""

    styled_summary = server_summary.style.applymap(highlight_rate, subset=["Backup_Success_Rate"])
    
    st.subheader(f"Servers at {location}")
    st.dataframe(styled_summary)

    # Pie Chart for Location Backup Success vs Failure
    success_location = server_summary["Backup_Success_Rate"].astype(float).apply(lambda x: x if x >= 95 else 0).sum()
    failure_location = server_summary["Backup_Success_Rate"].astype(float).apply(lambda x: 100 - x if x < 95 else 0).sum()

    fig_location = px.pie(
        names=["Success", "Failure"],
        values=[success_location, failure_location],
        title=f"Backup Success vs Failure at {location}",
        color=["Success", "Failure"],
        color_discrete_map={"Success": "green", "Failure": "red"},
    )

    st.plotly_chart(fig_location)

    # Level 2: Server Selection
    servers = location_df["Server"].unique()
    server = st.selectbox("Step 2: Select Server", servers)

    if server:
        server_df = location_df[location_df["Server"] == server]
        storage_nodes = server_df["Storage Node"].unique()

        st.subheader(f"Storage Nodes under {server}")
        st.table(pd.DataFrame({"Storage Node": storage_nodes}))

        # Level 3: Storage Node Selection
        storage_node = st.selectbox("Step 3: Select Storage Node", storage_nodes)

        if storage_node:
            node_df = server_df[server_df["Storage Node"] == storage_node]
            devices = node_df["Device"].unique()

            st.subheader(f"Devices under {storage_node}")
            st.table(pd.DataFrame({"Devices": devices}))

            # Level 4: Device Selection
            device = st.selectbox("Step 4: Select Device", devices)

            if device:
                device_df = node_df[node_df["Device"] == device].dropna(subset=["Month", "Used Space (TB)"])

                if not device_df.empty:
                    st.subheader(f"Storage Usage Chart for {device}")
                    usage_chart = device_df.set_index("Month")["Used Space (TB)"]
                    st.line_chart(usage_chart)

                    # Storage Summary
                    used_storage = device_df["Used Space (TB)"].sum()
                    available_storage = device_df["Available Storage (TB)"].sum()
                    st.success(f"**Total Used Storage for {device}:** {used_storage} TB")
                    st.info(f"**Total Available Storage for {device}:** {available_storage} TB")
                else:
                    st.warning("No usage data available for this device.")
