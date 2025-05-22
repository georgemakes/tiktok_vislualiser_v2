import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from tiktok_style import TikTokStyle


class BarChart:
    def __init__(self, style=None):
        self.fig = None
        self.style = style if style else TikTokStyle()

    def create_chart(self, data, x_axis, metrics, orientation='v', filters=None):
        if filters:
            for column, values in filters.items():
                if column in data.columns and values:
                    data = data[data[column].isin(values)]

        # Aggregate data to avoid multiple bars for same x-value
        grouped_data = data.groupby(x_axis)[metrics].sum().reset_index()

        # Hide zero values if option is enabled
        if self.style.hide_zero_values:
            # Create a mask to filter out rows with all zeros for selected metrics
            non_zero_mask = False
            for metric in metrics:
                non_zero_mask |= (grouped_data[metric] != 0)
            grouped_data = grouped_data[non_zero_mask]

        # Create figure
        self.fig = go.Figure()

        # Add traces for each metric
        for i, metric in enumerate(metrics):
            color = self.style.bar_colors[i % len(self.style.bar_colors)]  # Cycle through colors

            # If hiding zeros, filter them out for this specific metric
            metric_data = grouped_data.copy()
            if self.style.hide_zero_values:
                # Filter for this specific metric
                metric_data = metric_data[metric_data[metric] != 0]

            if orientation == 'v':
                self.fig.add_trace(
                    go.Bar(
                        x=metric_data[x_axis],
                        y=metric_data[metric],
                        name=metric,
                        marker_color=color
                    )
                )
            else:  # horizontal
                self.fig.add_trace(
                    go.Bar(
                        y=metric_data[x_axis],
                        x=metric_data[metric],
                        name=metric,
                        orientation='h',
                        marker_color=color
                    )
                )

        # Set layout
        if orientation == 'v':
            self.fig.update_layout(
                title=f"Multiple Metrics by {x_axis}",
                xaxis_title=x_axis,
                yaxis_title="Value"
            )
        else:
            self.fig.update_layout(
                title=f"Multiple Metrics by {x_axis}",
                yaxis_title=x_axis,
                xaxis_title="Value"
            )

        self._apply_style()

        return self.fig

    def _apply_style(self):
        if self.fig:
            # Get basic layout parameters
            layout_params = self.style.get_layout_params()

            # Add bar-specific parameters
            bar_params = self.style.get_bar_params()
            layout_params.update(bar_params)

            # Apply all layout parameters
            self.fig.update_layout(**layout_params)