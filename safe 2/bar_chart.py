import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from tiktok_style import TikTokStyle


class BarChart:
    def __init__(self, style=None, data_processor=None):
        self.fig = None
        self.style = style if style else TikTokStyle()
        self.data_processor = data_processor

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

        # Get metric types and labels
        metric_labels = {}
        if self.data_processor:
            for metric in metrics:
                metric_labels[metric] = self.data_processor.get_formatted_label(metric)

        # Add traces for each metric
        for i, metric in enumerate(metrics):
            color = self.style.bar_colors[i % len(self.style.bar_colors)]  # Cycle through colors

            # Get the proper label for this metric
            metric_label = metric_labels.get(metric, metric)

            # If hiding zeros, filter them out for this specific metric
            metric_data = grouped_data.copy()
            if self.style.hide_zero_values:
                # Filter for this specific metric
                metric_data = metric_data[metric_data[metric] != 0]

            # Get metric type for formatting
            metric_type = 'number'
            if self.data_processor:
                metric_type = self.data_processor.get_metric_type(metric)

            # Create hover template based on metric type
            hover_template = "%{y}"
            if orientation == 'h':
                hover_template = "%{x}"

            if metric_type == 'currency':
                hover_template = "£%{y:,.2f}" if orientation == 'v' else "£%{x:,.2f}"
            elif metric_type == 'percentage':
                hover_template = "%{y:.2f}%" if orientation == 'v' else "%{x:.2f}%"

            if orientation == 'v':
                self.fig.add_trace(
                    go.Bar(
                        x=metric_data[x_axis],
                        y=metric_data[metric],
                        name=metric_label,
                        marker_color=color,
                        hovertemplate=f"{x_axis}: %{{x}}<br>{metric_label}: {hover_template}<extra></extra>"
                    )
                )
            else:  # horizontal
                self.fig.add_trace(
                    go.Bar(
                        y=metric_data[x_axis],
                        x=metric_data[metric],
                        name=metric_label,
                        orientation='h',
                        marker_color=color,
                        hovertemplate=f"{x_axis}: %{{y}}<br>{metric_label}: {hover_template}<extra></extra>"
                    )
                )

        # Set axis labels and titles
        if orientation == 'v':
            # Get a combined title for y-axis based on all metrics
            if len(metrics) == 1 and metric_labels:
                y_title = metric_labels.get(metrics[0], metrics[0])
            else:
                y_title = "Value"

            # Configure axes
            self.fig.update_layout(
                title=f"Metrics by {x_axis}",
                xaxis_title=x_axis,
                yaxis_title=y_title
            )

            # Apply formatting to y-axis if it's a single metric
            if len(metrics) == 1 and self.data_processor:
                metric_type = self.data_processor.get_metric_type(metrics[0])
                if metric_type == 'currency':
                    self.fig.update_layout(
                        yaxis=dict(
                            tickprefix="£",
                            separatethousands=True
                        )
                    )
                elif metric_type == 'percentage':
                    self.fig.update_layout(
                        yaxis=dict(
                            ticksuffix="%",
                            tickformat=".2f"
                        )
                    )
        else:
            # Get a combined title for x-axis based on all metrics
            if len(metrics) == 1 and metric_labels:
                x_title = metric_labels.get(metrics[0], metrics[0])
            else:
                x_title = "Value"

            # Configure axes
            self.fig.update_layout(
                title=f"Metrics by {x_axis}",
                yaxis_title=x_axis,
                xaxis_title=x_title
            )

            # Apply formatting to x-axis if it's a single metric
            if len(metrics) == 1 and self.data_processor:
                metric_type = self.data_processor.get_metric_type(metrics[0])
                if metric_type == 'currency':
                    self.fig.update_layout(
                        xaxis=dict(
                            tickprefix="£",
                            separatethousands=True
                        )
                    )
                elif metric_type == 'percentage':
                    self.fig.update_layout(
                        xaxis=dict(
                            ticksuffix="%",
                            tickformat=".2f"
                        )
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