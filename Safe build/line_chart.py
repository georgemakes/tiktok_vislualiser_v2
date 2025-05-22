import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from tiktok_style import TikTokStyle


class LineChart:
    def __init__(self, style=None):
        self.fig = None
        self.style = style if style else TikTokStyle()

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

        # Handle zero values if hide_zero_values is enabled
        if self.style.hide_zero_values:
            if group_by and group_by in data.columns:
                # For grouped data, we need to carefully filter
                # First create the grouped data
                grouped_data = data.groupby([x_axis, group_by])[y_axis].sum().reset_index()
                # Then filter out zeros
                grouped_data = grouped_data[grouped_data[y_axis] != 0]
            else:
                # For non-grouped data, simply filter out zeros
                data = data[data[y_axis] != 0]
                grouped_data = data.groupby(x_axis)[y_axis].sum().reset_index()
                grouped_data = grouped_data[grouped_data[y_axis] != 0]
        else:
            # Normal aggregation without filtering zeros
            if group_by and group_by in data.columns:
                grouped_data = data.groupby([x_axis, group_by])[y_axis].sum().reset_index()
            else:
                grouped_data = data.groupby(x_axis)[y_axis].sum().reset_index()

        # Sort data chronologically for time series
        if pd.api.types.is_datetime64_any_dtype(grouped_data[x_axis]):
            grouped_data = grouped_data.sort_values(by=x_axis)

        # FIX: For grouped data, use plotly express with color_discrete_sequence
        if group_by and group_by in data.columns:
            self.fig = px.line(
                grouped_data,
                x=x_axis,
                y=y_axis,
                color=group_by,
                title=f"{y_axis} Over {x_axis}",
                markers=self.style.show_markers,  # Show/hide markers based on style
                line_shape=self.style.line_shape,  # Apply line shape (linear/spline)
                color_discrete_sequence=self.style.color_sequence  # Use style's color sequence
            )
        else:
            # FIX: For non-grouped data, use graph_objects.Figure for more control over colors
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
                    name=y_axis
                )
            )

            # Set the title
            self.fig.update_layout(title=f"{y_axis} Over {x_axis}")

        # Force x and y to be in the correct order for time series
        self.fig.update_layout(
            xaxis_title=x_axis,
            yaxis_title=y_axis
        )

        # Apply styling
        self._apply_style()

        return self.fig

    def _apply_style(self):
        if self.fig:
            # Apply layout parameters
            self.fig.update_layout(**self.style.get_layout_params())

            # For grouped data (using px.line), we need to update the traces differently
            if hasattr(self.fig, 'data') and len(self.fig.data) > 0 and hasattr(self.fig.data[0], 'mode'):
                # This is a plotly.graph_objects based figure with grouped data
                for trace in self.fig.data:
                    # Set marker visibility
                    if self.style.show_markers:
                        trace.mode = 'lines+markers'
                        trace.marker = self.style.get_marker_params()
                    else:
                        trace.mode = 'lines'
                        trace.marker = dict(size=0)

                    # Update line shape for all traces
                    if hasattr(trace, 'line'):
                        trace.line.shape = self.style.line_shape