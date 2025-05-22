import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from tiktok_style import TikTokStyle


class LineChart:
    def __init__(self, style=None, data_processor=None):
        self.fig = None
        self.style = style if style else TikTokStyle()
        self.data_processor = data_processor

    def create_chart(self, data, x_axis, y_axis, group_by=None, filters=None):
        # Apply filters if provided
        if filters:
            for column, values in filters.items():
                if column in data.columns and values:
                    data = data[data[column].isin(values)]

        # Ensure proper data formatting for time series data
        if 'date' in x_axis.lower() or 'day' in x_axis.lower():
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(data[x_axis]):
                try:
                    data[x_axis] = pd.to_datetime(data[x_axis])
                except:
                    pass  # If conversion fails, proceed with original data

        # Get metric type and format from data processor if available
        metric_type = 'number'
        y_axis_title = y_axis
        if self.data_processor:
            metric_type = self.data_processor.get_metric_type(y_axis)
            y_axis_title = self.data_processor.get_formatted_label(y_axis)

        # Handle zero values if hide_zero_values is enabled
        if self.style.hide_zero_values:
            # Create separate segments for each continuous section (when hiding zeros)
            if group_by and group_by in data.columns:
                # For grouped data

                # First get the grouped data
                grouped_data = data.groupby([x_axis, group_by])[y_axis].sum().reset_index()

                # Sort data chronologically for time series
                if pd.api.types.is_datetime64_any_dtype(grouped_data[x_axis]):
                    grouped_data = grouped_data.sort_values(by=[group_by, x_axis])

                # Filter out zeros
                grouped_data = grouped_data[grouped_data[y_axis] != 0]

                # Create figure that will hold all traces
                self.fig = go.Figure()

                # Get unique groups
                groups = grouped_data[group_by].unique()

                # For each group, identify gaps and create separate line segments
                for i, group_value in enumerate(groups):
                    # Get data for this group
                    group_data = grouped_data[grouped_data[group_by] == group_value]

                    # Sort by x-axis
                    group_data = group_data.sort_values(by=x_axis)

                    # Identify gaps where data points are too far apart
                    segments = self._split_into_continuous_segments(group_data, x_axis)

                    # Get the color for this group
                    color = self.style.color_sequence[i % len(self.style.color_sequence)]

                    # Create hover template based on metric type
                    hover_template = "%{y}"
                    if metric_type == 'currency':
                        hover_template = "£%{y:,.2f}"
                    elif metric_type == 'percentage':
                        hover_template = "%{y:.2f}%"

                    # Add each segment as a separate trace
                    for j, segment in enumerate(segments):
                        self.fig.add_trace(
                            go.Scatter(
                                x=segment[x_axis],
                                y=segment[y_axis],
                                mode='lines+markers' if self.style.show_markers else 'lines',
                                name=f"{group_value}" if j == 0 else f"{group_value} (cont.)",
                                showlegend=j == 0,  # Only show in legend once
                                line=dict(
                                    color=color,
                                    width=self.style.line_width,
                                    shape=self.style.line_shape
                                ),
                                marker=dict(
                                    size=self.style.marker_size if self.style.show_markers else 0,
                                    color=color
                                ),
                                legendgroup=str(group_value),  # Group in legend
                                hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis_title}: {hover_template}<extra></extra>"
                            )
                        )

                # Set the title
                self.fig.update_layout(title=f"{y_axis_title} Over {x_axis}")

            else:
                # For non-grouped data

                # Filter out zeros
                filtered_data = data[data[y_axis] != 0]

                # Group by x-axis and aggregate
                grouped_data = filtered_data.groupby(x_axis)[y_axis].sum().reset_index()

                # Sort data chronologically
                if pd.api.types.is_datetime64_any_dtype(grouped_data[x_axis]):
                    grouped_data = grouped_data.sort_values(by=x_axis)

                # Initialize figure
                self.fig = go.Figure()

                # Split into continuous segments
                segments = self._split_into_continuous_segments(grouped_data, x_axis)

                # Create hover template based on metric type
                hover_template = "%{y}"
                if metric_type == 'currency':
                    hover_template = "£%{y:,.2f}"
                elif metric_type == 'percentage':
                    hover_template = "%{y:.2f}%"

                # Add each segment as a separate trace
                for i, segment in enumerate(segments):
                    self.fig.add_trace(
                        go.Scatter(
                            x=segment[x_axis],
                            y=segment[y_axis],
                            mode='lines+markers' if self.style.show_markers else 'lines',
                            name=y_axis if i == 0 else f"{y_axis} (cont.)",
                            showlegend=i == 0,  # Only show in legend once
                            line=dict(
                                color=self.style.line_color,
                                width=self.style.line_width,
                                shape=self.style.line_shape
                            ),
                            marker=dict(
                                size=self.style.marker_size if self.style.show_markers else 0,
                                color=self.style.line_color
                            ),
                            hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis_title}: {hover_template}<extra></extra>"
                        )
                    )

                # Set the title
                self.fig.update_layout(title=f"{y_axis_title} Over {x_axis}")
        else:
            # Standard behavior when not hiding zeros (keep as before)
            if group_by and group_by in data.columns:
                # Group by x_axis and group_by, then aggregate y_axis
                grouped_data = data.groupby([x_axis, group_by])[y_axis].sum().reset_index()

                # Sort data chronologically for time series
                if pd.api.types.is_datetime64_any_dtype(grouped_data[x_axis]):
                    grouped_data = grouped_data.sort_values(by=x_axis)

                # Create the chart
                self.fig = px.line(
                    grouped_data,
                    x=x_axis,
                    y=y_axis,
                    color=group_by,
                    title=f"{y_axis_title} Over {x_axis}",
                    markers=self.style.show_markers,
                    line_shape=self.style.line_shape,
                    color_discrete_sequence=self.style.color_sequence
                )

                # Update hover template based on metric type
                if metric_type == 'currency':
                    self.fig.update_traces(
                        hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis_title}: £%{{y:,.2f}}<extra></extra>"
                    )
                elif metric_type == 'percentage':
                    self.fig.update_traces(
                        hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis_title}: %{{y:.2f}}%<extra></extra>"
                    )
            else:
                # Group by only x_axis and aggregate y_axis
                grouped_data = data.groupby(x_axis)[y_axis].sum().reset_index()

                # Sort data chronologically for time series
                if pd.api.types.is_datetime64_any_dtype(grouped_data[x_axis]):
                    grouped_data = grouped_data.sort_values(by=x_axis)

                # Create hover template based on metric type
                hover_template = "%{y}"
                if metric_type == 'currency':
                    hover_template = "£%{y:,.2f}"
                elif metric_type == 'percentage':
                    hover_template = "%{y:.2f}%"

                # Create figure
                self.fig = go.Figure()
                self.fig.add_trace(
                    go.Scatter(
                        x=grouped_data[x_axis],
                        y=grouped_data[y_axis],
                        mode='lines+markers' if self.style.show_markers else 'lines',
                        line=dict(
                            color=self.style.line_color,
                            width=self.style.line_width,
                            shape=self.style.line_shape
                        ),
                        marker=dict(
                            size=self.style.marker_size if self.style.show_markers else 0,
                            color=self.style.line_color
                        ),
                        name=y_axis,
                        hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis_title}: {hover_template}<extra></extra>"
                    )
                )

                # Set the title
                self.fig.update_layout(title=f"{y_axis_title} Over {x_axis}")

        # Set formatting for value axes based on metric type
        yaxis_config = dict(title=y_axis_title)

        # Add specific formatting for different metric types
        if metric_type == 'currency':
            yaxis_config.update(
                tickprefix="£",
                separatethousands=True
            )
        elif metric_type == 'percentage':
            yaxis_config.update(
                ticksuffix="%",
                tickformat=".2f"  # Format to 2 decimal places
            )

        # Force x and y to be in the correct order for time series with proper formatting
        self.fig.update_layout(
            xaxis_title=x_axis,
            yaxis=yaxis_config
        )

        # Apply styling
        self._apply_style()

        return self.fig

    def _split_into_continuous_segments(self, data, x_axis):
        """
        Split data into continuous segments where there are no large gaps
        This prevents connecting lines across gaps when zeros are hidden
        """
        if len(data) <= 1:
            return [data]  # Just one segment if there's 0 or 1 points

        # Sort data by x-axis
        data = data.sort_values(by=x_axis).reset_index(drop=True)

        # For datetime columns, compute the time difference between points
        if pd.api.types.is_datetime64_any_dtype(data[x_axis]):
            # Calculate time deltas between consecutive points
            time_deltas = data[x_axis].diff()

            # Find the median time delta as a reference
            median_delta = time_deltas.dropna().median()
            if pd.isna(median_delta) or median_delta.total_seconds() == 0:
                # If we can't determine a good threshold, default to not splitting
                return [data]

            # Define a large gap as 3x the median delta
            large_gap_threshold = median_delta * 3

            # Find the indexes where there are large gaps
            split_idx = time_deltas[time_deltas > large_gap_threshold].index.tolist()

        else:
            # For non-datetime columns, use value differences
            value_diffs = data[x_axis].diff()

            # Find the median difference as a reference
            median_diff = value_diffs.dropna().median()
            if pd.isna(median_diff) or median_diff == 0:
                # If we can't determine a good threshold, default to not splitting
                return [data]

            # Define a large gap as 3x the median difference
            large_gap_threshold = median_diff * 3

            # Find the indexes where there are large gaps
            split_idx = value_diffs[value_diffs > large_gap_threshold].index.tolist()

        # If no large gaps found, return the whole dataset as one segment
        if not split_idx:
            return [data]

        # Split the data into segments at the large gap points
        segments = []
        start_idx = 0

        for idx in split_idx:
            segments.append(data.loc[start_idx:idx - 1])
            start_idx = idx

        # Add the final segment
        segments.append(data.loc[start_idx:])

        return segments

    def _apply_style(self):
        if self.fig:
            # Apply layout parameters
            self.fig.update_layout(**self.style.get_layout_params())

            # For grouped data (using px.line), we need to update the traces differently
            if hasattr(self.fig, 'data') and len(self.fig.data) > 0 and hasattr(self.fig.data[0], 'mode'):
                # This is a plotly.graph_objects based figure
                for trace in self.fig.data:
                    # Update line shape for all traces
                    if hasattr(trace, 'line'):
                        trace.line.shape = self.style.line_shape