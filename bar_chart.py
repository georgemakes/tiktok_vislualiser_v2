import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
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

        # Aggregate data using proper methods for each metric
        grouped_data = self._aggregate_data_properly(data, x_axis, metrics)

        # Hide zero values if option is enabled
        if self.style.hide_zero_values:
            # Create a mask to filter out rows with all zeros for selected metrics
            non_zero_mask = False
            for metric in metrics:
                non_zero_mask |= (grouped_data[metric] != 0)
            grouped_data = grouped_data[non_zero_mask]

        # Check if we need to normalize metrics for better visualization
        needs_normalization = self._check_scaling_needs(grouped_data, metrics)

        # Create normalized data if needed
        if needs_normalization:
            normalized_data = self._normalize_metrics(grouped_data, metrics)
        else:
            normalized_data = grouped_data

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
            metric_data = normalized_data.copy()
            if self.style.hide_zero_values:
                # Filter for this specific metric
                metric_data = metric_data[metric_data[metric] != 0]

            # Get metric type for formatting
            metric_type = 'number'
            if self.data_processor:
                metric_type = self.data_processor.get_metric_type(metric)

            # Create hover template with original values
            if needs_normalization:
                # Use original values for hover
                custom_hover_text = []
                for idx, row in metric_data.iterrows():
                    original_idx = grouped_data[grouped_data[x_axis] == row[x_axis]].index[0]
                    original_value = grouped_data.loc[original_idx, metric]

                    if metric_type == 'currency':
                        formatted_value = f"£{original_value:,.2f}"
                    elif metric_type == 'percentage':
                        formatted_value = f"{original_value:.2f}%"
                    else:
                        formatted_value = f"{original_value:,.0f}"

                    custom_hover_text.append(f"{x_axis}: {row[x_axis]}<br>{metric_label}: {formatted_value}")
            else:
                # Standard hover template
                hover_template = "%{y}"
                if orientation == 'h':
                    hover_template = "%{x}"

                if metric_type == 'currency':
                    hover_template = "£%{y:,.2f}" if orientation == 'v' else "£%{x:,.2f}"
                elif metric_type == 'percentage':
                    hover_template = "%{y:.2f}%" if orientation == 'v' else "%{x:.2f}%"

            if orientation == 'v':
                bar_trace = go.Bar(
                    x=metric_data[x_axis],
                    y=metric_data[metric],
                    name=metric_label,
                    marker_color=color
                )

                if needs_normalization:
                    bar_trace.hovertext = custom_hover_text
                    bar_trace.hoverinfo = "text"
                else:
                    bar_trace.hovertemplate = f"{x_axis}: %{{x}}<br>{metric_label}: {hover_template}<extra></extra>"

                self.fig.add_trace(bar_trace)
            else:  # horizontal
                bar_trace = go.Bar(
                    y=metric_data[x_axis],
                    x=metric_data[metric],
                    name=metric_label,
                    orientation='h',
                    marker_color=color
                )

                if needs_normalization:
                    bar_trace.hovertext = custom_hover_text
                    bar_trace.hoverinfo = "text"
                else:
                    bar_trace.hovertemplate = f"{x_axis}: %{{y}}<br>{metric_label}: {hover_template}<extra></extra>"

                self.fig.add_trace(bar_trace)

        # Set axis labels and titles
        if orientation == 'v':
            # For normalized data, use a generic title
            if needs_normalization:
                y_title = "Relative Scale (Normalized)"
            elif len(metrics) == 1 and metric_labels:
                y_title = metric_labels.get(metrics[0], metrics[0])
            else:
                y_title = "Value"

            # Configure axes
            layout_config = {
                'title': f"Metrics by {x_axis}",
                'xaxis_title': x_axis,
                'yaxis_title': y_title
            }

            # Apply formatting to y-axis if it's a single metric and not normalized
            if len(metrics) == 1 and not needs_normalization and self.data_processor:
                metric_type = self.data_processor.get_metric_type(metrics[0])
                if metric_type == 'currency':
                    layout_config['yaxis'] = dict(
                        title=y_title,
                        tickprefix="£",
                        separatethousands=True
                    )
                elif metric_type == 'percentage':
                    layout_config['yaxis'] = dict(
                        title=y_title,
                        ticksuffix="%",
                        tickformat=".2f"
                    )

            self.fig.update_layout(**layout_config)
        else:
            # For normalized data, use a generic title
            if needs_normalization:
                x_title = "Relative Scale (Normalized)"
            elif len(metrics) == 1 and metric_labels:
                x_title = metric_labels.get(metrics[0], metrics[0])
            else:
                x_title = "Value"

            # Configure axes
            layout_config = {
                'title': f"Metrics by {x_axis}",
                'yaxis_title': x_axis,
                'xaxis_title': x_title
            }

            # Apply formatting to x-axis if it's a single metric and not normalized
            if len(metrics) == 1 and not needs_normalization and self.data_processor:
                metric_type = self.data_processor.get_metric_type(metrics[0])
                if metric_type == 'currency':
                    layout_config['xaxis'] = dict(
                        title=x_title,
                        tickprefix="£",
                        separatethousands=True
                    )
                elif metric_type == 'percentage':
                    layout_config['xaxis'] = dict(
                        title=x_title,
                        ticksuffix="%",
                        tickformat=".2f"
                    )

            self.fig.update_layout(**layout_config)

        self._apply_style()

        return self.fig

    def _aggregate_data_properly(self, data, x_axis, metrics):
        """Aggregate data using the appropriate method for each metric"""
        if not self.data_processor:
            # Fallback to sum if no data processor
            return data.groupby(x_axis)[metrics].sum().reset_index()

        # Group the data by x_axis
        grouped_data = data.groupby(x_axis)

        # Create aggregation dictionary
        agg_dict = {}
        for metric in metrics:
            aggregation_type = self.data_processor.get_aggregation_type(metric)
            if aggregation_type == 'average':
                agg_dict[metric] = 'mean'
            else:
                agg_dict[metric] = 'sum'

        # Apply aggregation
        result = grouped_data.agg(agg_dict).reset_index()

        return result

    def _check_scaling_needs(self, data, metrics):
        """Check if metrics have very different scales that would require normalization"""
        if len(metrics) <= 1:
            return False

        # Calculate the range (max - min) for each metric
        ranges = []
        for metric in metrics:
            metric_data = data[metric]
            if len(metric_data) > 0:
                metric_range = metric_data.max() - metric_data.min()
                if metric_range > 0:
                    ranges.append(metric_range)

        if len(ranges) <= 1:
            return False

        # Check if the ratio between largest and smallest range is > 100
        # This indicates very different scales (e.g., 0.03 vs 50000)
        max_range = max(ranges)
        min_range = min(ranges)

        if min_range == 0:
            return True  # One metric has no variation, definitely need normalization

        ratio = max_range / min_range
        return ratio > 10  # Threshold for when normalization is needed

    def _normalize_metrics(self, data, metrics):
        """Normalize metrics to 0-1 scale for better visualization"""
        normalized_data = data.copy()

        for metric in metrics:
            metric_data = data[metric]

            # Min-max normalization to 0-1 scale
            min_val = metric_data.min()
            max_val = metric_data.max()

            if max_val > min_val:
                # Scale to 0-100 for better visual representation
                normalized_data[metric] = ((metric_data - min_val) / (max_val - min_val)) * 100
            else:
                # If all values are the same, set to a constant
                normalized_data[metric] = 50  # Middle value

        return normalized_data

    def _apply_style(self):
        if self.fig:
            # Get basic layout parameters
            layout_params = self.style.get_layout_params()

            # Add bar-specific parameters
            bar_params = self.style.get_bar_params()
            layout_params.update(bar_params)

            # Apply all layout parameters
            self.fig.update_layout(**layout_params)