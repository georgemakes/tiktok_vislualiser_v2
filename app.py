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

st.set_page_config(page_title="GG Data Visualiser", page_icon="🎵", layout="wide")


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
    st.title("🎵 GG Data Visualiser")

    st.markdown("""
    <style>
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    .stSidebar {
        background-color: #111111 !important;
    }
    .stSelectbox label, .stMultiSelect label, .stFileUploader label {
        color: #ffffff !important;
    }
    .stMarkdown {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

        if not date_columns:
            st.warning("⚠️ No 'By Day' column detected. Please select a date column:")

            # Get all columns and let user pick one as date
            all_columns = list(data.columns)
            selected_date_col = st.selectbox(
                "Select Date Column",
                options=all_columns,
                help="Choose which column contains your dates"
            )

            if selected_date_col and st.button("Convert to Date"):
                try:
                    # Show preview of data before conversion
                    st.write("**Sample values from selected column:**")
                    st.write(data_processor.data[selected_date_col].head().tolist())

                    # Try multiple date formats for better conversion
                    date_formats = [
                        '%Y-%m-%d',  # 2024-01-01
                        '%Y-%m',  # 2025-01 (month only)
                        '%d/%m/%Y',  # 01/01/2024
                        '%m/%d/%Y',  # 01/01/2024
                        '%d-%m-%Y',  # 01-01-2024
                        '%Y/%m',  # 2025/01 (month only)
                        '%Y-%m-%d %H:%M:%S',  # With time
                        None  # Let pandas infer
                    ]

                    converted = False
                    for fmt in date_formats:
                        try:
                            if fmt:
                                data_processor.data[selected_date_col] = pd.to_datetime(
                                    data_processor.data[selected_date_col],
                                    format=fmt,
                                    errors='coerce'
                                )
                            else:
                                data_processor.data[selected_date_col] = pd.to_datetime(
                                    data_processor.data[selected_date_col],
                                    errors='coerce',
                                    infer_datetime_format=True
                                )

                            # Check if conversion worked
                            if data_processor.data[selected_date_col].notna().sum() > 0:
                                converted = True
                                break
                        except:
                            continue

                    if converted:
                        data_processor.date_columns.append(selected_date_col)
                        date_columns = data_processor.get_date_columns()
                        st.success(f"✅ Converted '{selected_date_col}' to date column!")
                        st.rerun()
                    else:
                        st.error("❌ Could not convert column to dates. Check the format.")

                except Exception as e:
                    st.error(f"❌ Conversion failed: {str(e)}")

        # Continue with existing filters and charts...

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
            # Shuffle Colors Button - RIGHT BEFORE CHARTS

            # Chart-specific settings
            if chart_type == "Line Chart":
                with style_container.expander("Line Chart Style", expanded=True):
                    style.line_width = st.slider("Line Width", 1, 5, style.line_width, key="line_width_slider")

                    # Multi-line colors from style guide
                    st.markdown("**Line Colors:**")

                    # Initialize session state with style guide colors
                    if 'custom_line_colors' not in st.session_state:
                        st.session_state.custom_line_colors = style.color_sequence[:8].copy()

                    # Initialize secondary axis color
                    if 'secondary_axis_color' not in st.session_state:
                        st.session_state.secondary_axis_color = "#ff0050"  # Default TikTok red

                    # Randomize colors button
                    if st.button("🎲 Randomize Colors", key="randomize_multiline_colors"):
                        import random
                        tiktok_palette = style.bar_colors.copy()
                        new_colors = random.sample(tiktok_palette, min(8, len(tiktok_palette)))

                        # Update session state
                        st.session_state.custom_line_colors = new_colors
                        st.session_state.secondary_axis_color = random.choice(tiktok_palette)
                        style.color_sequence = new_colors
                        style.line_color = new_colors[0]
                        st.success("🎨 Colors randomized!")

                    # Show color pickers for first 8 colors
                    for i in range(8):
                        default_color = style.color_sequence[i] if i < len(style.color_sequence) else "#fe2c56"

                        color = st.color_picker(
                            f"Line {i + 1} Color",
                            st.session_state.custom_line_colors[i] if i < len(
                                st.session_state.custom_line_colors) else default_color,
                            key=f"multiline_color_{i}"
                        )

                        if len(st.session_state.custom_line_colors) <= i:
                            st.session_state.custom_line_colors.append(color)
                        else:
                            st.session_state.custom_line_colors[i] = color

                    # Secondary axis color picker
                    st.markdown("**Secondary Y-Axis Color:**")
                    new_secondary_color = st.color_picker(
                        "Secondary Axis Line Color",
                        style.secondary_axis_color,
                        key="secondary_axis_color_picker"
                    )

                    # Apply immediately when changed
                    if new_secondary_color != style.secondary_axis_color:
                        style.secondary_axis_color = new_secondary_color


                    # Apply colors to style
                    style.color_sequence = st.session_state.custom_line_colors.copy()
                    style.line_color = st.session_state.custom_line_colors[0]

                    # Line specific options
                    style.show_markers = st.checkbox("Show Data Points", value=style.show_markers,
                                                     key="show_data_points_line")
                    if style.show_markers:
                        style.marker_size = st.slider("Marker Size", 4, 12, style.marker_size, key="marker_size_line")

                    line_shape_options = {
                        "Linear": "linear",
                        "Spline (Curved)": "spline",
                        "Stepped (Horizontal First)": "hv",
                        "Stepped (Vertical First)": "vh"
                    }
                    selected_shape = st.selectbox(
                        "Line Shape",
                        options=list(line_shape_options.keys()),
                        index=list(line_shape_options.values()).index(style.line_shape),
                        key="line_shape_selector"
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

        # Metric Override Tab - AFTER FILTERS, BEFORE CHARTS
        st.subheader("⚙️ Advanced Settings")
        with st.expander("Metric Aggregation & Formatting Override", expanded=False):
            st.markdown("**Configure how metrics are calculated and displayed:**")

            # Initialize session state for overrides if not exists
            if 'metric_overrides' not in st.session_state:
                st.session_state.metric_overrides = {}

            for metric in metrics:
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    # Get current setting (either overridden or auto-detected)
                    if metric in st.session_state.metric_overrides:
                        current_agg = st.session_state.metric_overrides[metric]['agg']
                    else:
                        current_agg = data_processor.get_aggregation_type(metric)

                    new_agg = st.selectbox(
                        f"{metric} - Aggregation",
                        options=["sum", "average"],
                        index=1 if current_agg == "average" else 0,
                        key=f"agg_{metric}"
                    )

                with col2:
                    # Get current type (either overridden or auto-detected)
                    if metric in st.session_state.metric_overrides:
                        current_type = st.session_state.metric_overrides[metric]['type']
                    else:
                        current_type = data_processor.get_metric_type(metric)

                    new_type = st.selectbox(
                        "Format Type",
                        options=["number", "currency", "percentage"],
                        index=["number", "currency", "percentage"].index(current_type),
                        key=f"type_{metric}"
                    )

                with col3:
                    decimal_places = st.selectbox(
                        "Decimals",
                        options=[0, 1, 2, 3],
                        index=2,
                        key=f"decimals_{metric}"
                    )

                # Apply overrides to data processor
                data_processor.aggregation_types[metric] = new_agg
                data_processor.metric_types[metric] = new_type

                # Store in session state
                st.session_state.metric_overrides[metric] = {
                    'agg': new_agg,
                    'type': new_type,
                    'decimals': decimal_places
                }

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

        # Metric Override Tab
        # Metric Override Tab
        # Metric Override Tab

        # OVERVIEW METRICS SECTION - ENHANCED FOR GROUPING
        st.markdown("---")

        # Metric selection for overview
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📊 Campaign Overview")
        with col2:
            if st.button("⚙️ Configure Metrics", key="config_overview_metrics"):
                if 'show_metric_config' not in st.session_state:
                    st.session_state.show_metric_config = False
                st.session_state.show_metric_config = not st.session_state.show_metric_config

        # Metric configuration
        if st.session_state.get('show_metric_config', False):
            st.markdown("**Select metrics to display in overview:**")

            # Initialize selected metrics if not exists
            if 'selected_overview_metrics' not in st.session_state:
                st.session_state.selected_overview_metrics = metrics.copy()

            # Create removable metric tags
            metric_cols = st.columns(4)
            for i, metric in enumerate(metrics):
                with metric_cols[i % 4]:
                    is_selected = metric in st.session_state.selected_overview_metrics

                    if st.checkbox(
                            metric.replace('_', ' ').title(),
                            value=is_selected,
                            key=f"overview_metric_{metric}"
                    ):
                        if metric not in st.session_state.selected_overview_metrics:
                            st.session_state.selected_overview_metrics.append(metric)
                    else:
                        if metric in st.session_state.selected_overview_metrics:
                            st.session_state.selected_overview_metrics.remove(metric)

            # Quick action buttons
            button_cols = st.columns(3)
            with button_cols[0]:
                if st.button("Select All", key="select_all_metrics"):
                    st.session_state.selected_overview_metrics = metrics.copy()
                    st.rerun()
            with button_cols[1]:
                if st.button("Select None", key="select_no_metrics"):
                    st.session_state.selected_overview_metrics = []
                    st.rerun()
            with button_cols[2]:
                if st.button("Reset to Default", key="reset_metrics"):
                    st.session_state.selected_overview_metrics = metrics.copy()
                    st.rerun()

        # Get selected metrics for display
        display_metrics = st.session_state.get('selected_overview_metrics', metrics)

        if not display_metrics:
            st.info("🔍 No metrics selected for overview. Click 'Configure Metrics' to select some.")
        else:
            # Calculate overview metrics
            if group_by and group_by in filtered_data.columns:
                # GROUPED OVERVIEW WITH TOTAL TAB
                st.markdown(f"**Metrics by {group_by}:**")

                # Get unique groups
                groups = filtered_data[group_by].unique()

                # Create tabs including Total tab
                tab_names = ["📋 Total"] + [str(group) for group in groups]
                tabs = st.tabs(tab_names)

                # Store all group metrics for comparison
                comparison_data = []

                # TOTAL TAB
                with tabs[0]:
                    st.markdown("**Overall Totals Across All Groups:**")

                    # Calculate total metrics
                    total_metrics = {}
                    for metric in display_metrics:
                        agg_type = data_processor.get_aggregation_type(metric)
                        if agg_type == 'average':
                            total_metrics[metric] = filtered_data[metric].mean()
                        else:
                            total_metrics[metric] = filtered_data[metric].sum()

                    # Display total metrics
                    cols = st.columns(min(4, len(total_metrics)))

                    for j, (metric, value) in enumerate(total_metrics.items()):
                        with cols[j % 4]:
                            # Format based on metric type
                            metric_type = data_processor.get_metric_type(metric)

                            if metric_type == 'currency':
                                formatted_value = f"£{value:,.2f}"
                            elif metric_type == 'percentage':
                                formatted_value = f"{value:.2f}%"
                            else:
                                if value >= 1000000:
                                    formatted_value = f"{value / 1000000:.1f}M"
                                elif value >= 1000:
                                    formatted_value = f"{value / 1000:.1f}K"
                                else:
                                    formatted_value = f"{value:,.0f}"

                            # Use TikTok pink for total
                            st.markdown(f"""
                            <div style="
                                background-color: #111111; 
                                padding: 15px; 
                                border-radius: 8px; 
                                border-left: 4px solid #fe2c56;
                                margin-bottom: 10px;
                            ">
                                <h5 style="color: #ffffff; margin: 0; font-size: 12px;">
                                    {metric.replace('_', ' ').title()}
                                </h5>
                                <h2 style="color: #fe2c56; margin: 5px 0 0 0; font-size: 28px; font-weight: bold;">
                                    {formatted_value}
                                </h2>
                            </div>
                            """, unsafe_allow_html=True)

                # GROUP TABS
                for i, (tab, group_value) in enumerate(zip(tabs[1:], groups)):
                    with tab:
                        # Filter data for this group
                        group_data = filtered_data[filtered_data[group_by] == group_value]

                        # Calculate metrics for this group
                        group_metrics = {}
                        for metric in display_metrics:
                            agg_type = data_processor.get_aggregation_type(metric)
                            if agg_type == 'average':
                                group_metrics[metric] = group_data[metric].mean()
                            else:
                                group_metrics[metric] = group_data[metric].sum()

                        # Store for comparison
                        comparison_data.append({group_by: group_value, **group_metrics})

                        # Display metrics in cards with group colors
                        cols = st.columns(min(4, len(group_metrics)))
                        group_color = st.session_state.custom_line_colors[i % len(
                            st.session_state.custom_line_colors)] if 'custom_line_colors' in st.session_state else \
                        style.color_sequence[i % len(style.color_sequence)]

                        for j, (metric, value) in enumerate(group_metrics.items()):
                            with cols[j % 4]:
                                # Format based on metric type
                                metric_type = data_processor.get_metric_type(metric)

                                if metric_type == 'currency':
                                    formatted_value = f"£{value:,.2f}"
                                elif metric_type == 'percentage':
                                    formatted_value = f"{value:.2f}%"
                                else:
                                    if value >= 1000000:
                                        formatted_value = f"{value / 1000000:.1f}M"
                                    elif value >= 1000:
                                        formatted_value = f"{value / 1000:.1f}K"
                                    else:
                                        formatted_value = f"{value:,.0f}"

                                # Custom styling with group color
                                st.markdown(f"""
                                <div style="
                                    background-color: #111111; 
                                    padding: 15px; 
                                    border-radius: 8px; 
                                    border-left: 4px solid {group_color};
                                    margin-bottom: 10px;
                                ">
                                    <h5 style="color: #ffffff; margin: 0; font-size: 12px;">
                                        {metric.replace('_', ' ').title()}
                                    </h5>
                                    <h2 style="color: {group_color}; margin: 5px 0 0 0; font-size: 24px; font-weight: bold;">
                                        {formatted_value}
                                    </h2>
                                </div>
                                """, unsafe_allow_html=True)

                # Comparison table (after tabs)
                # Comparison table (after tabs) WITH FLIP OPTION
                if comparison_data and len(comparison_data) > 1:
                    st.markdown("### 📋 Comparison Table")

                    # Add flip comparison option
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        comparison_df = pd.DataFrame(comparison_data)
                    with col2:
                        if st.button("🔄 Flip Comparison", key="flip_comparison"):
                            if 'comparison_flipped' not in st.session_state:
                                st.session_state.comparison_flipped = False
                            st.session_state.comparison_flipped = not st.session_state.comparison_flipped

                    # Format the dataframe for display
                    formatted_df = comparison_df.copy()
                    for metric in display_metrics:
                        if metric in formatted_df.columns:
                            metric_type = data_processor.get_metric_type(metric)
                            if metric_type == 'currency':
                                formatted_df[metric] = formatted_df[metric].apply(lambda x: f"£{x:,.2f}")
                            elif metric_type == 'percentage':
                                formatted_df[metric] = formatted_df[metric].apply(lambda x: f"{x:.2f}%")
                            else:
                                formatted_df[metric] = formatted_df[metric].apply(
                                    lambda x: f"{x:,.0f}" if x >= 1 else f"{x:.2f}")

                    st.dataframe(formatted_df, use_container_width=True)

                    # Calculate % changes WITH FLIP LOGIC
                    if len(comparison_data) > 1:
                        # Determine base group based on flip state
                        flipped = st.session_state.get('comparison_flipped', False)

                        if flipped:
                            st.markdown(f"### 📈 % Change vs Last Group ({comparison_data[-1][group_by]})")
                            base_group = comparison_data[-1]  # Use last group as base
                            compare_groups = comparison_data[:-1]  # Compare all others to last
                        else:
                            st.markdown(f"### 📈 % Change vs First Group ({comparison_data[0][group_by]})")
                            base_group = comparison_data[0]  # Use first group as base
                            compare_groups = comparison_data[1:]  # Compare all others to first

                        change_data = []
                        for group_data in compare_groups:
                            change_row = {group_by: group_data[group_by]}
                            for metric in display_metrics:
                                if metric in base_group and metric in group_data:
                                    base_value = base_group[metric]
                                    current_value = group_data[metric]
                                    if base_value != 0:
                                        pct_change = ((current_value - base_value) / base_value) * 100
                                        # Color code the percentage
                                        if pct_change > 0:
                                            change_row[metric] = f"🟢 +{pct_change:.1f}%"
                                        elif pct_change < 0:
                                            change_row[metric] = f"🔴 {pct_change:.1f}%"
                                        else:
                                            change_row[metric] = f"⚪ 0.0%"
                                    else:
                                        change_row[metric] = "❓ N/A"
                            change_data.append(change_row)

                        if change_data:
                            change_df = pd.DataFrame(change_data)
                            st.dataframe(change_df, use_container_width=True)


            else:
                # NON-GROUPED OVERVIEW - Nice cards like before
                overview_metrics = {}
                for metric in display_metrics:
                    agg_type = data_processor.get_aggregation_type(metric)
                    if agg_type == 'average':
                        overview_metrics[metric] = filtered_data[metric].mean()
                    else:
                        overview_metrics[metric] = filtered_data[metric].sum()
                # Display in columns with nice cards
                cols = st.columns(min(4, len(overview_metrics)))
                for i, (metric, value) in enumerate(overview_metrics.items()):
                    with cols[i % 4]:
                        # Format based on metric type
                        metric_type = data_processor.get_metric_type(metric)
                        if metric_type == 'currency':
                            formatted_value = f"£{value:,.2f}"
                        elif metric_type == 'percentage':
                            formatted_value = f"{value:.2f}%"
                        else:
                            if value >= 1000000:
                                formatted_value = f"{value / 1000000:.1f}M"
                            elif value >= 1000:
                                formatted_value = f"{value / 1000:.1f}K"
                            else:
                                formatted_value = f"{value:,.0f}"
                        # Custom styling with TikTok colors (sa as grouped)
                        st.markdown(f"""
                            <div style="
                                background-color: #111111; 
                                padding: 20px; 
                                border-radius: 10px; 
                                border-left: 4px solid #fe2c56;
                                margin-bottom: 10px;
                            ">
                                <h4 style="color: #ffffff; margin: 0; font-size: 14px;">
                                    {metric.replace('_', ' ').title()}
                                </h4>
                                <h1 style="color: #fe2c56; margin: 5px 0 0 0; font-size: 36px; font-weight: bold;">
                                    {formatted_value}
                                </h1>
                            </div>
                            """, unsafe_allow_html=True)
        st.write("Data Preview:")

        st.dataframe(filtered_data.head())

        # Show row count
        st.write(f"**Rows in filtered data:** {len(filtered_data)}")

        # DATA EXPORT REPORT BUTTON
        st.markdown("---")
        st.subheader("📋 Export Full Report")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("**Export complete analysis including data, filters, charts, and insights**")

        with col2:
            export_format = st.selectbox("Format", ["Detailed Text", "JSON Data", "CSV + Summary"])

        with col3:
            if st.button("📤 Generate Report", key="export_full_report"):
                # Generate comprehensive report
                report_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "file_info": {
                        "filename": uploaded_file.name if uploaded_file else "Unknown",
                        "total_rows": len(data),
                        "filtered_rows": len(filtered_data),
                        "date_range": {
                            col: {
                                "start": data_processor.get_date_range(col)[0].strftime("%Y-%m-%d") if
                                data_processor.get_date_range(col)[0] else None,
                                "end": data_processor.get_date_range(col)[1].strftime("%Y-%m-%d") if
                                data_processor.get_date_range(col)[1] else None
                            } for col in date_columns
                        }
                    },
                    "applied_filters": {
                        "date_filters": {col: f"{start.date()} to {end.date()}" for col, (start, end) in
                                         date_range_filters.items()},
                        "dimension_filters": {col: values for col, values in filters.items() if values}
                    },
                    "chart_configuration": {
                        "type": chart_type,
                        "x_axis": locals().get('x_axis', 'Not set'),
                        "y_axis": locals().get('y_axis', 'Not set'),
                        "secondary_y_axis": locals().get('secondary_y_axis', None),
                        "group_by": locals().get('group_by', None),
                        "hide_zero_values": style.hide_zero_values,
                        "show_markers": style.show_markers
                    },
                    "data_insights": {
                        "metrics_summary": {},
                        "top_performers": {},
                        "data_quality": {}
                    },
                    "overview_metrics": {},
                    "raw_data_sample": filtered_data.head(100).to_dict('records') if len(filtered_data) > 0 else []
                }

                # Calculate insights
                for metric in display_metrics:
                    metric_data = filtered_data[metric].dropna()
                    if len(metric_data) > 0:
                        agg_type = data_processor.get_aggregation_type(metric)
                        metric_type = data_processor.get_metric_type(metric)

                        total_value = metric_data.sum() if agg_type == 'sum' else metric_data.mean()

                        report_data["overview_metrics"][metric] = {
                            "value": float(total_value),
                            "type": metric_type,
                            "aggregation": agg_type,
                            "formatted": f"£{total_value:,.2f}" if metric_type == 'currency' else f"{total_value:.2f}%" if metric_type == 'percentage' else f"{total_value:,.0f}"
                        }

                        report_data["data_insights"]["metrics_summary"][metric] = {
                            "min": float(metric_data.min()),
                            "max": float(metric_data.max()),
                            "mean": float(metric_data.mean()),
                            "median": float(metric_data.median()),
                            "std": float(metric_data.std()) if len(metric_data) > 1 else 0,
                            "null_count": int(filtered_data[metric].isnull().sum()),
                            "zero_count": int((filtered_data[metric] == 0).sum())
                        }

                # Top performers by group
                if group_by and group_by in filtered_data.columns:
                    for metric in display_metrics[:3]:  # Top 3 metrics only
                        group_performance = filtered_data.groupby(group_by)[metric].agg(
                            data_processor.get_aggregation_type(metric) if data_processor.get_aggregation_type(
                                metric) == 'mean' else 'sum'
                        ).sort_values(ascending=False)

                        report_data["data_insights"]["top_performers"][metric] = {
                            "best": {
                                "group": str(group_performance.index[0]),
                                "value": float(group_performance.iloc[0])
                            },
                            "worst": {
                                "group": str(group_performance.index[-1]),
                                "value": float(group_performance.iloc[-1])
                            }
                        }

                # Data quality insights
                report_data["data_insights"]["data_quality"] = {
                    "completeness": {
                        metric: f"{(1 - filtered_data[metric].isnull().sum() / len(filtered_data)) * 100:.1f}%"
                        for metric in metrics
                    },
                    "date_coverage": {
                        col: f"{(data_processor.get_date_range(col)[1] - data_processor.get_date_range(col)[0]).days} days"
                        for col in date_columns if data_processor.get_date_range(col)[0]
                    }
                }

                if export_format == "Detailed Text":
                    # Generate human-readable report
                    report_text = f"""
# TikTok Ad Analysis Report
Generated: {report_data['timestamp']}

## 📊 Data Overview
- **File**: {report_data['file_info']['filename']}
- **Total Records**: {report_data['file_info']['total_rows']:,}
- **Filtered Records**: {report_data['file_info']['filtered_rows']:,}
- **Data Completeness**: {(report_data['file_info']['filtered_rows'] / report_data['file_info']['total_rows'] * 100):.1f}% of original data

## 🔍 Applied Filters
"""

                    if report_data['applied_filters']['date_filters']:
                        report_text += "**Date Filters:**\n"
                        for col, range_str in report_data['applied_filters']['date_filters'].items():
                            report_text += f"- {col}: {range_str}\n"

                    if report_data['applied_filters']['dimension_filters']:
                        report_text += "\n**Dimension Filters:**\n"
                        for col, values in report_data['applied_filters']['dimension_filters'].items():
                            report_text += f"- {col}: {', '.join(map(str, values))}\n"

                    report_text += f"""
## 📈 Chart Configuration
- **Type**: {report_data['chart_configuration']['type']}
- **X-Axis**: {report_data['chart_configuration']['x_axis']}
- **Y-Axis**: {report_data['chart_configuration']['y_axis']}"""

                    if report_data['chart_configuration']['secondary_y_axis']:
                        report_text += f"\n- **Secondary Y-Axis**: {report_data['chart_configuration']['secondary_y_axis']}"

                    if report_data['chart_configuration']['group_by']:
                        report_text += f"\n- **Grouped By**: {report_data['chart_configuration']['group_by']}"

                    report_text += f"""
- **Hide Zero Values**: {report_data['chart_configuration']['hide_zero_values']}

## 📊 Key Metrics Summary
"""

                    for metric, data in report_data['overview_metrics'].items():
                        report_text += f"**{metric.replace('_', ' ').title()}**: {data['formatted']} ({data['aggregation']})\n"

                    report_text += "\n## 🎯 Performance Insights\n"

                    for metric, performers in report_data['data_insights']['top_performers'].items():
                        report_text += f"**{metric.replace('_', ' ').title()}**:\n"
                        report_text += f"- Best: {performers['best']['group']} ({performers['best']['value']:,.2f})\n"
                        report_text += f"- Worst: {performers['worst']['group']} ({performers['worst']['value']:,.2f})\n\n"

                    report_text += "\n## 📋 Data Quality\n"
                    for metric, completeness in report_data['data_insights']['data_quality']['completeness'].items():
                        report_text += f"- {metric}: {completeness} complete\n"

                    # Download button
                    st.download_button(
                        label="💾 Download Text Report",
                        data=report_text,
                        file_name=f"tiktok_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )

                elif export_format == "JSON Data":
                    # JSON format for programmatic analysis
                    import json
                    json_data = json.dumps(report_data, indent=2, default=str)

                    st.download_button(
                        label="💾 Download JSON Report",
                        data=json_data,
                        file_name=f"tiktok_analysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

                elif export_format == "CSV + Summary":
                    # CSV data + summary
                    csv_data = filtered_data.to_csv(index=False)

                    summary = f"""Summary Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
File: {report_data['file_info']['filename']}
Records: {len(filtered_data):,}
Chart: {chart_type}
Filters Applied: {len([f for f in [*filters.values(), *date_range_filters.values()] if f])}

Key Metrics:
"""
                    for metric, data in report_data['overview_metrics'].items():
                        summary += f"{metric}: {data['formatted']}\n"

                    # Create zip with both files
                    import zipfile
                    import io

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        zip_file.writestr("filtered_data.csv", csv_data)
                        zip_file.writestr("summary.txt", summary)
                        zip_file.writestr("full_report.json", json.dumps(report_data, indent=2, default=str))

                    st.download_button(
                        label="💾 Download ZIP Package",
                        data=zip_buffer.getvalue(),
                        file_name=f"tiktok_analysis_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )

                st.success("✅ Report generated! Use the download button above.")

                # Show preview
                with st.expander("📋 Report Preview", expanded=False):
                    if export_format == "Detailed Text":
                        st.text(report_text[:2000] + "..." if len(report_text) > 2000 else report_text)
                    elif export_format == "JSON Data":
                        st.json(report_data)
                    else:
                        st.write("**Package Contents:**")
                        st.write("- filtered_data.csv: Your filtered dataset")
                        st.write("- summary.txt: Key insights summary")
                        st.write("- full_report.json: Complete analysis data")

if __name__ == "__main__":
    main()