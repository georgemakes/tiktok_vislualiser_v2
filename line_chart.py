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

    def create_chart(self, data, x_axis, y_axis, group_by=None, filters=None, secondary_y_axis=None):
        # Apply filters if provided
        if filters:
            for column, values in filters.items():
                if column in data.columns and values:
                    data = data[data[column].isin(values)]

        # Ensure proper data formatting for time series data
        if 'date' in x_axis.lower() or 'day' in x_axis.lower():
            if not pd.api.types.is_datetime64_any_dtype(data[x_axis]):
                try:
                    data[x_axis] = pd.to_datetime(data[x_axis])
                except:
                    pass

        # Get metric type and format from data processor if available
        metric_type = 'number'
        y_axis_title = y_axis
        if self.data_processor:
            metric_type = self.data_processor.get_metric_type(y_axis)
            y_axis_title = self.data_processor.get_formatted_label(y_axis)

        # Secondary y-axis information
        secondary_metric_type = None
        secondary_y_axis_title = None

        if secondary_y_axis:
            if self.data_processor:
                secondary_metric_type = self.data_processor.get_metric_type(secondary_y_axis)
                secondary_y_axis_title = self.data_processor.get_formatted_label(secondary_y_axis)
            else:
                secondary_metric_type = 'number'
                secondary_y_axis_title = secondary_y_axis

        # Initialize figure
        self.fig = go.Figure()

        # Handle zero values if hide_zero_values is enabled
        if self.style.hide_zero_values:
            if group_by and group_by in data.columns:
                self._add_grouped_data_with_zero_handling(data, x_axis, y_axis, group_by, metric_type, y_axis_title, False)
                if secondary_y_axis:
                    self._add_grouped_data_with_zero_handling(data, x_axis, secondary_y_axis, group_by, secondary_metric_type, secondary_y_axis_title, True)
            else:
                self._add_ungrouped_data_with_zero_handling(data, x_axis, y_axis, metric_type, y_axis_title, False)
                if secondary_y_axis:
                    self._add_ungrouped_data_with_zero_handling(data, x_axis, secondary_y_axis, secondary_metric_type, secondary_y_axis_title, True)
        else:
            # Standard behavior when not hiding zeros
            if group_by and group_by in data.columns:
                # PRIMARY Y-AXIS TRACES
                grouped_data_primary = self._aggregate_data_properly(data, [x_axis, group_by], [y_axis])
                if pd.api.types.is_datetime64_any_dtype(grouped_data_primary[x_axis]):
                    grouped_data_primary = grouped_data_primary.sort_values(by=x_axis)

                groups = grouped_data_primary[group_by].unique()

                # Add PRIMARY traces first
                for i, group_value in enumerate(groups):
                    group_data = grouped_data_primary[grouped_data_primary[group_by] == group_value]
                    color = self.style.color_sequence[i % len(self.style.color_sequence)]

                    hover_template = "%{y}"
                    if metric_type == 'currency':
                        hover_template = "£%{y:,.2f}"
                    elif metric_type == 'percentage':
                        hover_template = "%{y:.2f}%"

                    self.fig.add_trace(
                        go.Scatter(
                            x=group_data[x_axis],
                            y=group_data[y_axis],
                            mode='lines+markers' if self.style.show_markers else 'lines',
                            name=f"{group_value} - {y_axis}",
                            line=dict(
                                color=color,
                                width=self.style.line_width,
                                shape=self.style.line_shape
                            ),
                            marker=dict(
                                size=self.style.marker_size if self.style.show_markers else 0,
                                color=color
                            ),
                            hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis_title}: {hover_template}<extra></extra>"
                        )
                    )

                # SECONDARY Y-AXIS TRACES
                if secondary_y_axis:
                    grouped_data_secondary = self._aggregate_data_properly(data, [x_axis, group_by], [secondary_y_axis])
                    if pd.api.types.is_datetime64_any_dtype(grouped_data_secondary[x_axis]):
                        grouped_data_secondary = grouped_data_secondary.sort_values(by=x_axis)

                    for i, group_value in enumerate(groups):
                        group_data = grouped_data_secondary[grouped_data_secondary[group_by] == group_value]
                        # Use SAME color as primary but make it secondary axis
                        color = self.style.color_sequence[i % len(self.style.color_sequence)]

                        hover_template = "%{y}"
                        if secondary_metric_type == 'currency':
                            hover_template = "£%{y:,.2f}"
                        elif secondary_metric_type == 'percentage':
                            hover_template = "%{y:.2f}%"

                        self.fig.add_trace(
                            go.Scatter(
                                x=group_data[x_axis],
                                y=group_data[secondary_y_axis],
                                mode='lines+markers' if self.style.show_markers else 'lines',
                                name=f"{group_value} - {secondary_y_axis}",
                                line=dict(
                                    color=color,
                                    width=self.style.line_width,
                                    shape=self.style.line_shape,
                                    dash='dash'
                                ),
                                marker=dict(
                                    size=self.style.marker_size if self.style.show_markers else 0,
                                    color=color,
                                    symbol='square'
                                ),
                                hovertemplate=f"{x_axis}: %{{x}}<br>{secondary_y_axis_title}: {hover_template}<extra></extra>",
                                yaxis="y2"
                            )
                        )
            else:
                # NON-GROUPED DATA
                grouped_data_primary = self._aggregate_data_properly(data, [x_axis], [y_axis])
                if pd.api.types.is_datetime64_any_dtype(grouped_data_primary[x_axis]):
                    grouped_data_primary = grouped_data_primary.sort_values(by=x_axis)

                hover_template = "%{y}"
                if metric_type == 'currency':
                    hover_template = "£%{y:,.2f}"
                elif metric_type == 'percentage':
                    hover_template = "%{y:.2f}%"

                # Add PRIMARY trace
                self.fig.add_trace(
                    go.Scatter(
                        x=grouped_data_primary[x_axis],
                        y=grouped_data_primary[y_axis],
                        mode='lines+markers' if self.style.show_markers else 'lines',
                        name=y_axis,
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

                # Add SECONDARY trace
                if secondary_y_axis:
                    grouped_data_secondary = self._aggregate_data_properly(data, [x_axis], [secondary_y_axis])
                    if pd.api.types.is_datetime64_any_dtype(grouped_data_secondary[x_axis]):
                        grouped_data_secondary = grouped_data_secondary.sort_values(by=x_axis)

                    hover_template = "%{y}"
                    if secondary_metric_type == 'currency':
                        hover_template = "£%{y:,.2f}"
                    elif secondary_metric_type == 'percentage':
                        hover_template = "%{y:.2f}%"

                    # Use SECONDARY AXIS COLOR (separate from grouped colors)
                    secondary_color = self.style.secondary_axis_color

                    self.fig.add_trace(
                        go.Scatter(
                            x=grouped_data_secondary[x_axis],
                            y=grouped_data_secondary[secondary_y_axis],
                            mode='lines+markers' if self.style.show_markers else 'lines',
                            name=secondary_y_axis,
                            line=dict(
                                color=secondary_color,
                                width=self.style.line_width,
                                shape=self.style.line_shape,
                                dash='dash'
                            ),
                            marker=dict(
                                size=self.style.marker_size if self.style.show_markers else 0,
                                color=secondary_color,
                                symbol='square'
                            ),
                            hovertemplate=f"{x_axis}: %{{x}}<br>{secondary_y_axis_title}: {hover_template}<extra></extra>",
                            yaxis="y2"
                        )
                    )

        # Set the chart title
        if secondary_y_axis:
            self.fig.update_layout(title=f"{y_axis_title} vs {secondary_y_axis_title} Over {x_axis}")
        else:
            self.fig.update_layout(title=f"{y_axis_title} Over {x_axis}")

        # Set formatting for axes based on metric types
        self._configure_axes(x_axis, y_axis, y_axis_title, metric_type, secondary_y_axis, secondary_y_axis_title, secondary_metric_type)

        # Apply styling
        self._apply_style()

        return self.fig

    def _aggregate_data_properly(self, data, group_columns, metrics):
        """Aggregate data using the appropriate method for each metric"""
        if not self.data_processor:
            return data.groupby(group_columns)[metrics].sum().reset_index()

        grouped_data = data.groupby(group_columns)
        agg_dict = {}
        for metric in metrics:
            aggregation_type = self.data_processor.get_aggregation_type(metric)
            if aggregation_type == 'average':
                agg_dict[metric] = 'mean'
            else:
                agg_dict[metric] = 'sum'

        result = grouped_data.agg(agg_dict).reset_index()
        return result

    def _add_grouped_data_with_zero_handling(self, data, x_axis, y_axis, group_by, metric_type, y_axis_title, is_secondary=False):
        """Add traces for grouped data with zero handling"""
        grouped_data = self._aggregate_data_properly(data, [x_axis, group_by], [y_axis])

        if pd.api.types.is_datetime64_any_dtype(grouped_data[x_axis]):
            grouped_data = grouped_data.sort_values(by=[group_by, x_axis])

        grouped_data = grouped_data[grouped_data[y_axis] != 0]
        groups = grouped_data[group_by].unique()

        for i, group_value in enumerate(groups):
            group_data = grouped_data[grouped_data[group_by] == group_value]
            group_data = group_data.sort_values(by=x_axis)
            segments = self._split_into_continuous_segments(group_data, x_axis)

            # Use proper color logic
            if is_secondary:
                color = self.style.color_sequence[i % len(self.style.color_sequence)]  # Same as primary group
            else:
                color = self.style.color_sequence[i % len(self.style.color_sequence)]

            hover_template = "%{y}"
            if metric_type == 'currency':
                hover_template = "£%{y:,.2f}"
            elif metric_type == 'percentage':
                hover_template = "%{y:.2f}%"

            for j, segment in enumerate(segments):
                trace_config = {
                    'x': segment[x_axis],
                    'y': segment[y_axis],
                    'mode': 'lines+markers' if self.style.show_markers else 'lines',
                    'name': f"{group_value} - {y_axis}" if j == 0 else f"{group_value} - {y_axis} (cont.)",
                    'showlegend': j == 0,
                    'line': dict(
                        color=color,
                        width=self.style.line_width,
                        shape=self.style.line_shape
                    ),
                    'marker': dict(
                        size=self.style.marker_size if self.style.show_markers else 0,
                        color=color
                    ),
                    'legendgroup': f"{group_value}-{y_axis}",
                    'hovertemplate': f"{x_axis}: %{{x}}<br>{y_axis_title}: {hover_template}<extra></extra>"
                }

                if is_secondary:
                    trace_config['yaxis'] = 'y2'
                    trace_config['line']['dash'] = 'dash'
                    trace_config['marker']['symbol'] = 'square'

                self.fig.add_trace(go.Scatter(**trace_config))

    def _add_ungrouped_data_with_zero_handling(self, data, x_axis, y_axis, metric_type, y_axis_title, is_secondary=False):
        """Add traces for ungrouped data with zero handling"""
        filtered_data = data[data[y_axis] != 0]
        grouped_data = self._aggregate_data_properly(filtered_data, [x_axis], [y_axis])

        if pd.api.types.is_datetime64_any_dtype(grouped_data[x_axis]):
            grouped_data = grouped_data.sort_values(by=x_axis)

        segments = self._split_into_continuous_segments(grouped_data, x_axis)

        hover_template = "%{y}"
        if metric_type == 'currency':
            hover_template = "£%{y:,.2f}"
        elif metric_type == 'percentage':
            hover_template = "%{y:.2f}%"

        color = self.style.line_color
        if is_secondary:
            color = self.style.secondary_axis_color

        for i, segment in enumerate(segments):
            trace_config = {
                'x': segment[x_axis],
                'y': segment[y_axis],
                'mode': 'lines+markers' if self.style.show_markers else 'lines',
                'name': y_axis if i == 0 else f"{y_axis} (cont.)",
                'showlegend': i == 0,
                'line': dict(
                    color=color,
                    width=self.style.line_width,
                    shape=self.style.line_shape
                ),
                'marker': dict(
                    size=self.style.marker_size if self.style.show_markers else 0,
                    color=color
                ),
                'hovertemplate': f"{x_axis}: %{{x}}<br>{y_axis_title}: {hover_template}<extra></extra>"
            }

            if is_secondary:
                trace_config['yaxis'] = 'y2'
                trace_config['line']['dash'] = 'dash'
                trace_config['marker']['symbol'] = 'square'

            self.fig.add_trace(go.Scatter(**trace_config))

    def _configure_axes(self, x_axis, y_axis, y_axis_title, metric_type, secondary_y_axis=None, secondary_y_axis_title=None, secondary_metric_type=None):
        """Configure axis titles and formatting based on metric types"""
        yaxis_config = dict(
            title=dict(
                text=y_axis_title,
                font=dict(color=self.style.text_color)
            ),
            tickfont=dict(color=self.style.text_color)
        )

        if metric_type == 'currency':
            yaxis_config.update(tickprefix="£", separatethousands=True)
        elif metric_type == 'percentage':
            yaxis_config.update(ticksuffix="%", tickformat=".2f")

        layout_update = {
            'xaxis_title': x_axis,
            'yaxis': yaxis_config
        }

        if secondary_y_axis:
            secondary_yaxis_config = dict(
                title=dict(
                    text=secondary_y_axis_title,
                    font=dict(color=self.style.text_color)
                ),
                tickfont=dict(color=self.style.text_color),
                overlaying="y",
                side="right",
                nticks=5,
                showgrid=False
            )

            if secondary_metric_type == 'currency':
                secondary_yaxis_config.update(tickprefix="£", separatethousands=True)
            elif secondary_metric_type == 'percentage':
                secondary_yaxis_config.update(ticksuffix="%", tickformat=".2f")

            layout_update['yaxis2'] = secondary_yaxis_config

        self.fig.update_layout(**layout_update)

    def _split_into_continuous_segments(self, data, x_axis):
        """Split data into continuous segments where there are no large gaps"""
        if len(data) <= 1:
            return [data]

        data = data.sort_values(by=x_axis).reset_index(drop=True)

        if pd.api.types.is_datetime64_any_dtype(data[x_axis]):
            time_deltas = data[x_axis].diff()
            median_delta = time_deltas.dropna().median()
            if pd.isna(median_delta) or median_delta.total_seconds() == 0:
                return [data]
            large_gap_threshold = median_delta * 3
            split_idx = time_deltas[time_deltas > large_gap_threshold].index.tolist()
        else:
            value_diffs = data[x_axis].diff()
            median_diff = value_diffs.dropna().median()
            if pd.isna(median_diff) or median_diff == 0:
                return [data]
            large_gap_threshold = median_diff * 3
            split_idx = value_diffs[value_diffs > large_gap_threshold].index.tolist()

        if not split_idx:
            return [data]

        segments = []
        start_idx = 0

        for idx in split_idx:
            segments.append(data.loc[start_idx:idx - 1])
            start_idx = idx

        segments.append(data.loc[start_idx:])
        return segments

    def _apply_style(self):
        if self.fig:
            self.fig.update_layout(**self.style.get_layout_params())

            if hasattr(self.fig, 'data') and len(self.fig.data) > 0 and hasattr(self.fig.data[0], 'mode'):
                for trace in self.fig.data:
                    if hasattr(trace, 'line'):
                        trace.line.shape = self.style.line_shape