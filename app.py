import streamlit as st
import pandas as pd
import os
import sys
import json
import time
from datetime import datetime, timedelta

# Import the modules from the current directory
from data_processor import DataProcessor
from line_chart import LineChart
from bar_chart import BarChart
from heatmap import HeatMap
from tiktok_style import TikTokStyle

st.set_page_config(page_title="TikTok Ad Report Analyzer", layout="wide")


def load_preferences():
    """Load saved user preferences if they exist"""
    try:
        # Create a preferences directory if it doesn't exist
        os.makedirs('preferences', exist_ok=True)

        # Check if preferences file exists
        if os.path.exists('preferences/style_preferences.json'):
            with open('preferences/style_preferences.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        st.sidebar.warning(f"Could not load preferences: {e}")

    return None


def save_preferences(style_dict):
    """Save user preferences to a file"""
    try:
        # Create a preferences directory if it doesn't exist
        os.makedirs('preferences', exist_ok=True)

        # Save preferences to a file
        with open('preferences/style_preferences.json', 'w') as f:
            json.dump(style_dict, f, indent=4)

        return True
    except Exception as e:
        st.sidebar.warning(f"Could not save preferences: {e}")
        return False


def main():
    st.title("TikTok Ad Report Analyzer")

    # Initialize session state variables if they don't exist
    if 'style' not in st.session_state:
        # Try to load saved preferences
        saved_prefs = load_preferences()
        if saved_prefs:
            st.session_state.style = TikTokStyle.from_dict(saved_prefs)
        else:
            st.session_state.style = TikTokStyle()

    # Add a session state for the success message
    if 'show_success' not in st.session_state:
        st.session_state.show_success = False

    style = st.session_state.style

    uploaded_file = st.file_uploader("Upload TikTok Ad Report", type=["xlsx", "csv"])

    if uploaded_file is not None:
        data_processor = DataProcessor()
        with st.spinner("Loading and processing data..."):
            try:
                data = data_processor.load_data(uploaded_file)
                st.session_state.show_success = True
                # Use empty to create a container for the success message
                success_container = st.empty()
                if st.session_state.show_success:
                    success_container.success("File loaded successfully!")
                    # Schedule the message to disappear after 3 seconds
                    time.sleep(3)
                    success_container.empty()
                    st.session_state.show_success = False
            except Exception as e:
                st.error(f"Error loading file: {e}")
                return

        metrics = data_processor.get_metrics()
        dimensions = data_processor.get_dimensions()
        date_columns = data_processor.get_date_columns()

        # ----- SIDEBAR ORGANIZATION -----
        st.sidebar.header("Data Visualization")

        # First: Chart type selection
        chart_type = st.sidebar.selectbox("Select Chart Type", ["Line Chart", "Bar Chart", "Heat Map"])

        # Create containers for different sidebar sections
        date_filter_container = st.sidebar.container()
        dimension_filter_container = st.sidebar.container()
        style_container = st.sidebar.container()

        # ----- 1. DATE RANGE FILTERS FIRST -----
        date_filter_container.subheader("Date Filters")

        # Date range filters
        date_range_filters = {}

        # Show date range filters if date columns exist
        if date_columns:
            for date_col in date_columns:
                with date_filter_container.expander(f"Filter by {date_col}", expanded=True):
                    min_date, max_date = data_processor.get_date_range(date_col)
                    if min_date and max_date:
                        # Create a date range slider
                        use_date_filter = st.checkbox(f"Apply filter for {date_col}", key=f"use_{date_col}")

                        if use_date_filter:
                            # Get the timestamp versions
                            max_date_ts = pd.Timestamp(max_date)
                            min_date_ts = pd.Timestamp(min_date)

                            # Show date inputs
                            col1, col2 = st.columns(2)
                            with col1:
                                start_date = st.date_input(
                                    f"Start {date_col}",
                                    min_date_ts.date() if hasattr(min_date_ts, 'date') else min_date,
                                    min_value=min_date_ts.date() if hasattr(min_date_ts, 'date') else min_date,
                                    max_value=max_date_ts.date() if hasattr(max_date_ts, 'date') else max_date,
                                    key=f"start_{date_col}"
                                )
                            with col2:
                                end_date = st.date_input(
                                    f"End {date_col}",
                                    max_date_ts.date() if hasattr(max_date_ts, 'date') else max_date,
                                    min_value=min_date_ts.date() if hasattr(min_date_ts, 'date') else min_date,
                                    max_value=max_date_ts.date() if hasattr(max_date_ts, 'date') else max_date,
                                    key=f"end_{date_col}"
                                )

                            # Add preset buttons for common date ranges
                            preset_cols = st.columns(4)

                            with preset_cols[0]:
                                if st.button("Last 7d", key=f"7d_{date_col}"):
                                    start_date = (max_date_ts - pd.Timedelta(days=7)).date()
                                    end_date = max_date_ts.date()

                            with preset_cols[1]:
                                if st.button("Last 30d", key=f"30d_{date_col}"):
                                    start_date = (max_date_ts - pd.Timedelta(days=30)).date()
                                    end_date = max_date_ts.date()

                            with preset_cols[2]:
                                if st.button("Last 90d", key=f"90d_{date_col}"):
                                    start_date = (max_date_ts - pd.Timedelta(days=90)).date()
                                    end_date = max_date_ts.date()

                            with preset_cols[3]:
                                if st.button("All", key=f"all_{date_col}"):
                                    start_date = min_date_ts.date() if hasattr(min_date_ts, 'date') else min_date
                                    end_date = max_date_ts.date() if hasattr(max_date_ts, 'date') else max_date

                            # Convert date objects to pandas timestamps for filtering
                            start_ts = pd.Timestamp(start_date)
                            end_ts = pd.Timestamp(end_date)

                            # Store the date range for filtering
                            date_range_filters[date_col] = (start_ts, end_ts)
        else:
            date_filter_container.info("No date columns detected in your data.")

        # ----- 2. DIMENSION FILTERS SECOND -----
        dimension_filter_container.subheader("Dimension Filters")

        # Regular dimension filters
        non_date_dimensions = [col for col in dimensions if col not in date_columns]
        filter_cols = dimension_filter_container.multiselect("Select Dimensions to Filter By", non_date_dimensions)
        filters = {}

        for col in filter_cols:
            unique_values = data_processor.get_unique_values(col)
            selected_values = dimension_filter_container.multiselect(f"Select {col}", unique_values)
            filters[col] = selected_values

        # ----- 3. STYLE CUSTOMIZATION LAST -----
        style_container.subheader("Customization")

        # General visualization options
        with style_container.expander("General Options", expanded=False):
            # Zero value handling
            style.hide_zero_values = st.checkbox("Hide Zero Values", value=style.hide_zero_values)

            # Chart width control
            chart_width = st.slider("Chart Width", min_value=600, max_value=2000, value=1200, step=50,
                                    help="Adjust chart width to accommodate long labels")

        # Allow customization of style
        if style_container.checkbox("Customize Style"):
            # Basic style settings
            style.background_color = style_container.color_picker("Background Color", style.background_color)
            style.text_color = style_container.color_picker("Text Color", style.text_color)
            style.grid_color = style_container.color_picker("Grid Color", style.grid_color)

            # Font and size settings
            style.title_font_size = style_container.slider("Title Font Size", 10, 24, style.title_font_size)
            style.text_font_size = style_container.slider("Text Font Size", 8, 18, style.text_font_size)

            # Chart-specific settings
            if chart_type == "Line Chart":
                with style_container.expander("Line Chart Style", expanded=True):
                    style.line_color = st.color_picker("Line Color", style.line_color)
                    style.line_width = st.slider("Line Width", 1, 5, style.line_width)

                    # Line specific options
                    style.show_markers = st.checkbox("Show Data Points", value=style.show_markers)
                    if style.show_markers:
                        style.marker_size = st.slider("Marker Size", 4, 12, style.marker_size)

                    line_shape_options = {
                        "Linear": "linear",
                        "Spline (Curved)": "spline",
                        "Stepped (Horizontal First)": "hv",
                        "Stepped (Vertical First)": "vh"
                    }
                    selected_shape = st.selectbox(
                        "Line Shape",
                        options=list(line_shape_options.keys()),
                        index=list(line_shape_options.values()).index(style.line_shape)
                    )
                    style.line_shape = line_shape_options[selected_shape]

            elif chart_type == "Bar Chart":
                with style_container.expander("Bar Chart Style", expanded=True):
                    # Custom bar colors with multiselect
                    st.text("Bar Colors")
                    colors = ["#00f2ea", "#ff0050", "#ccff00", "#ee1d52", "#69c9d0", "#ffffff", "#000000", "#ff0000",
                              "#00ff00", "#0000ff"]
                    selected_colors = []

                    # Display color pickers for each bar color (up to 5)
                    for i in range(min(5, len(style.bar_colors))):
                        color_key = f"bar_color_{i}"
                        selected_colors.append(st.color_picker(f"Color {i + 1}", style.bar_colors[i] if i < len(
                            style.bar_colors) else "#ffffff"))

                    style.bar_colors = selected_colors
                    style.color_sequence = selected_colors  # Use same colors for color sequence

            elif chart_type == "Heat Map":
                with style_container.expander("Heat Map Style", expanded=True):
                    colorscale_options = ["viridis", "plasma", "inferno", "magma", "cividis", "turbo",
                                          "blues", "greens", "reds", "purples", "oranges", "bluered", "rdbu"]
                    style.colorscale = st.selectbox("Color Scale", colorscale_options,
                                                    index=colorscale_options.index(style.colorscale))

            # Save preferences button
            if style_container.button("Save as Default"):
                if save_preferences(style.to_dict()):
                    style_container.success("Preferences saved successfully!")

        # Apply both regular filters and date range filters
        filtered_data = data_processor.filter_data(filters, date_range_filters)

        # Show applied filters
        if filters or date_range_filters:
            with st.expander("Applied Filters", expanded=True):
                # Create columns for better display
                if date_range_filters:
                    st.subheader("Date Filters")
                    for col, (start, end) in date_range_filters.items():
                        st.write(f"**{col}**: {start.date()} to {end.date()}")

                if filters:
                    st.subheader("Dimension Filters")
                    for col, values in filters.items():
                        if values:
                            st.write(f"**{col}**: {', '.join(str(v) for v in values)}")

        # Identify date columns explicitly
        non_date_dimensions = [col for col in dimensions if col not in date_columns]

        if chart_type == "Line Chart":
            st.subheader("Line Chart Settings")

            # For line charts, date columns should be prioritized for the x-axis
            if date_columns:
                default_x = date_columns[0]  # Default to first date column
                x_axis = st.selectbox("Select X-Axis (Time Dimension)",
                                      date_columns + non_date_dimensions,
                                      index=0,  # Default to first date column
                                      key="line_x")
            else:
                x_axis = st.selectbox("Select X-Axis", dimensions, key="line_x")

            # Primary y-axis
            y_axis = st.selectbox("Select Y-Axis (Metric)", metrics, key="line_y")

            # Secondary y-axis
            use_secondary_y = st.checkbox("Add Secondary Y-Axis", key="use_secondary_y")
            secondary_y_axis = None
            if use_secondary_y:
                # Filter out the primary y-axis from the options
                secondary_metrics = [m for m in metrics if m != y_axis]
                if secondary_metrics:
                    secondary_y_axis = st.selectbox("Select Secondary Y-Axis (Metric)",
                                                    secondary_metrics,
                                                    key="line_secondary_y")

            group_by = st.selectbox("Group By (Optional)", ["None"] + non_date_dimensions, key="line_group")

            if group_by == "None":
                group_by = None

            # Create line chart with data processor for currency/percentage formatting
            line_chart = LineChart(style=style, data_processor=data_processor)
            fig = line_chart.create_chart(filtered_data, x_axis, y_axis, group_by, secondary_y_axis=secondary_y_axis)

            # Apply chart width
            fig.update_layout(width=chart_width)
            st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': True})

        elif chart_type == "Bar Chart":
            st.subheader("Bar Chart Settings")

            # For bar charts, non-date dimensions make more sense on the x-axis
            x_axis = st.selectbox("Select X-Axis (Dimension)",
                                  non_date_dimensions if non_date_dimensions else dimensions,
                                  key="bar_x")

            y_metrics = st.multiselect("Select Metrics", metrics, key="bar_y")
            orientation = st.radio("Orientation", ["Vertical", "Horizontal"])

            if y_metrics:
                # Create bar chart with data processor for currency/percentage formatting
                bar_chart = BarChart(style=style, data_processor=data_processor)
                fig = bar_chart.create_chart(
                    filtered_data,
                    x_axis,
                    y_metrics,
                    orientation="v" if orientation == "Vertical" else "h"
                )
                # Apply chart width
                fig.update_layout(width=chart_width)
                st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': True})
            else:
                st.warning("Please select at least one metric for the bar chart.")

        elif chart_type == "Heat Map":
            st.subheader("Heat Map Settings")

            # For heatmaps, default to a date dimension for x-axis if available
            if date_columns:
                x_axis = st.selectbox("Select X-Axis",
                                      date_columns + non_date_dimensions,
                                      index=0,  # Default to first date
                                      key="hm_x")
            else:
                x_axis = st.selectbox("Select X-Axis", dimensions, key="hm_x")

            # For y-axis, prioritize non-date dimensions
            y_axis = st.selectbox("Select Y-Axis",
                                  non_date_dimensions if non_date_dimensions else dimensions,
                                  key="hm_y")

            metric = st.selectbox("Select Metric", metrics, key="hm_metric")

            if x_axis != y_axis:
                # Create heatmap with data processor for currency/percentage formatting
                heatmap = HeatMap(style=style, data_processor=data_processor)
                fig = heatmap.create_chart(filtered_data, x_axis, y_axis, metric)
                # Apply chart width
                fig.update_layout(width=chart_width)
                st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': True})
            else:
                st.warning("Please select different dimensions for X and Y axes.")

        # Add save chart button
        if st.button("Save Chart"):
            # Get the figure from the appropriate chart type
            if chart_type == "Line Chart":
                fig = line_chart.fig
            elif chart_type == "Bar Chart" and y_metrics:
                fig = bar_chart.fig
            elif chart_type == "Heat Map" and x_axis != y_axis:
                fig = heatmap.fig
            else:
                st.warning("No valid chart to save")
                return

            # Create charts directory if it doesn't exist
            os.makedirs('charts', exist_ok=True)

            # Generate filename based on chart type and metrics
            if chart_type == "Line Chart" and secondary_y_axis:
                filename = f"charts/tiktok_{chart_type.lower().replace(' ', '_')}_{x_axis}_{y_axis}_vs_{secondary_y_axis}.html"
            elif chart_type == "Bar Chart":
                metrics_str = "_".join(y_metrics)
                filename = f"charts/tiktok_{chart_type.lower().replace(' ', '_')}_{x_axis}_{metrics_str}.html"
            else:
                filename = f"charts/tiktok_{chart_type.lower().replace(' ', '_')}_{x_axis}_{y_axis if 'y_axis' in locals() else metric}.html"

            # Save the figure as HTML
            try:
                fig.write_html(filename)
                st.success(f"Chart saved as {filename}")
            except Exception as e:
                st.error(f"Error saving chart: {e}")

        # MOVED Data Preview to after the charts
        st.write("Data Preview:")
        st.dataframe(filtered_data.head())

        # Show row count
        st.write(f"**Rows in filtered data:** {len(filtered_data)}")


if __name__ == "__main__":
    main()