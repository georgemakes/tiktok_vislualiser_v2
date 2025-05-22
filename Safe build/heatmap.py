import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from tiktok_style import TikTokStyle


class HeatMap:
    def __init__(self, style=None):
        self.fig = None
        self.style = style if style else TikTokStyle()

    def create_chart(self, data, x_axis, y_axis, metric, filters=None):
        if filters:
            for column, values in filters.items():
                if column in data.columns and values:
                    data = data[data[column].isin(values)]

        # Sort data if using dates on x-axis
        if 'date' in x_axis.lower() or 'day' in x_axis.lower():
            if hasattr(data[x_axis], 'dt'):  # Check if it's a datetime column
                data = data.sort_values(by=x_axis)

        # Hide zero values if enabled
        if self.style.hide_zero_values:
            data = data[data[metric] != 0]

        # Create pivot table
        pivot_data = data.pivot_table(
            values=metric,
            index=y_axis,
            columns=x_axis,
            aggfunc='mean',
            fill_value=np.nan if self.style.hide_zero_values else 0
        )

        # Replace zeros with NaN to hide them in the heatmap if hide_zero_values is enabled
        if self.style.hide_zero_values:
            pivot_data = pivot_data.replace(0, np.nan)

        # Create the heatmap
        self.fig = px.imshow(
            pivot_data,
            labels=dict(x=x_axis, y=y_axis, color=metric),
            title=f"{metric} by {x_axis} and {y_axis}",
            color_continuous_scale=self.style.colorscale,  # Apply custom colorscale
        )

        # Apply styling
        self._apply_style()

        return self.fig

    def _apply_style(self):
        if self.fig:
            # Get base layout parameters
            layout_params = self.style.get_layout_params()

            # Add color axis parameters
            layout_params["coloraxis"] = self.style.get_coloraxis_params()

            # Apply layout parameters
            self.fig.update_layout(**layout_params)

            # Make sure x and y axis labels are readable
            self.fig.update_xaxes(
                tickangle=45,
                tickfont=dict(color=self.style.text_color),
                title_font=dict(color=self.style.text_color)
            )

            self.fig.update_yaxes(
                tickfont=dict(color=self.style.text_color),
                title_font=dict(color=self.style.text_color)
            )