import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re


class DataProcessor:
    def __init__(self):
        self.data = None
        self.metrics = []
        self.dimensions = []
        self.date_columns = []
        self.metric_types = {}  # To store the type of each metric (currency, percentage, etc.)
        self.aggregation_types = {}  # To store how metrics should be aggregated (sum, average)

    def load_data(self, file):
        """
        Load data from an uploaded file (CSV or Excel)
        Works with either a string path or a Streamlit UploadedFile object
        """
        # Handle Streamlit UploadedFile objects
        if hasattr(file, 'name'):
            # This is a Streamlit UploadedFile object
            file_name = file.name.lower()
            if file_name.endswith('.xlsx'):
                self.data = pd.read_excel(file)
            elif file_name.endswith('.csv'):
                self.data = pd.read_csv(file)
            else:
                raise ValueError("Unsupported file format. Please use .xlsx or .csv")
        else:
            # This is a regular file path string
            file_path = str(file).lower()
            if file_path.endswith('.xlsx'):
                self.data = pd.read_excel(file)
            elif file_path.endswith('.csv'):
                self.data = pd.read_csv(file)
            else:
                raise ValueError("Unsupported file format. Please use .xlsx or .csv")

        # Automatically detect and convert date columns
        self._convert_date_columns()
        self._identify_columns()
        self._identify_metric_types()
        return self.data

    def _convert_date_columns(self):
        """
        Automatically detect and convert columns that might contain dates
        Handles multiple date formats
        """
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY or MM-DD-YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY or MM/DD/YYYY
            r'\d{1,2}/\d{1,2}/\d{2}',  # DD/MM/YY or MM/DD/YY
            r'\d{1,2}\s+[a-zA-Z]{3,}\s+\d{4}',  # DD Month YYYY
            r'[a-zA-Z]{3,}\s+\d{1,2},?\s+\d{4}'  # Month DD, YYYY
        ]

        for col in self.data.columns:
            # Check if column name suggests it might be a date
            col_lower = col.lower()
            if any(hint in col_lower for hint in ['date', 'day', 'time', 'month', 'year']):
                # Get first non-null value to check if it looks like a date
                if self.data[col].notna().any():
                    sample_value = str(self.data[col].dropna().iloc[0])

                    # Check if it matches any date pattern
                    is_date_like = any(re.search(pattern, sample_value) for pattern in date_patterns)

                    if is_date_like:
                        try:
                            # Try to convert using pandas
                            self.data[col] = pd.to_datetime(self.data[col], errors='coerce')

                            # Keep track of date columns
                            if self.data[col].notna().any():  # Only add if conversion worked
                                self.date_columns.append(col)

                        except:
                            pass  # Skip if conversion fails

    def _identify_columns(self):
        # First identify date columns from automatic detection
        date_cols = [col for col in self.data.columns if pd.api.types.is_datetime64_any_dtype(self.data[col])]
        self.date_columns = list(set(self.date_columns + date_cols))

        # Then identify numeric columns (metrics)
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()

        # Set metrics and dimensions
        self.metrics = numeric_cols
        self.dimensions = [col for col in self.data.columns if col not in numeric_cols or col in date_cols]

    def _identify_metric_types(self):
        """Identify metric types and aggregation methods based on their names and patterns"""

        # Define patterns for different types of metrics
        currency_patterns = [
            'cost', 'spend', 'revenue', 'budget', 'value', 'conversion_value', 'roas', 'rar'
        ]

        # Cost-per-X metrics (currency but should be averaged, not summed)
        cost_per_patterns = [
            'cpm', 'cpc', 'cpa', 'cpv', 'cpl', 'cpi', 'cost_per'
        ]

        percentage_patterns = [
            'cvr', 'ctr', 'rate', 'percent', '%', 'ratio', 'frequency',
            'engagement_rate', 'conversion_rate', 'view_rate', 'completion_rate',
            'bounce_rate', 'click_through_rate'
        ]

        # Count/volume metrics (should be summed)
        count_patterns = [
            'impressions', 'clicks', 'views', 'reach', 'conversions', 'leads',
            'purchases', 'installs', 'downloads', 'shares', 'likes', 'comments',
            'sessions', 'users', 'visitors', 'pageviews', 'orders', 'transactions'
        ]

        # Time-based metrics (should be averaged)
        time_patterns = [
            'watch_time', 'session_duration', 'time_on_page', 'duration',
            'avg_time', 'average_time'
        ]

        for metric in self.metrics:
            metric_lower = metric.lower()

            # Check aggregation type and metric type
            if any(pattern in metric_lower for pattern in cost_per_patterns):
                self.metric_types[metric] = 'currency'
                self.aggregation_types[metric] = 'average'  # CPCs should be averaged
            elif any(pattern in metric_lower for pattern in currency_patterns):
                self.metric_types[metric] = 'currency'
                self.aggregation_types[metric] = 'sum'  # Costs/revenue should be summed
            elif any(pattern in metric_lower for pattern in percentage_patterns):
                self.metric_types[metric] = 'percentage'
                self.aggregation_types[metric] = 'average'  # Rates should be averaged
            elif any(pattern in metric_lower for pattern in count_patterns):
                self.metric_types[metric] = 'number'
                self.aggregation_types[metric] = 'sum'  # Counts should be summed
            elif any(pattern in metric_lower for pattern in time_patterns):
                self.metric_types[metric] = 'number'
                self.aggregation_types[metric] = 'average'  # Time metrics should be averaged
            else:
                # Default behavior
                self.metric_types[metric] = 'number'
                self.aggregation_types[metric] = 'sum'  # Default to sum

    def filter_data(self, filters, date_range_filters=None):
        """
        Filter data based on categorical filters and date range filters

        Args:
            filters (dict): Dictionary mapping column names to lists of allowed values
            date_range_filters (dict): Dictionary mapping date column names to tuples of (start_date, end_date)

        Returns:
            pandas.DataFrame: Filtered data
        """
        filtered_data = self.data.copy()

        # Apply categorical filters
        for column, values in filters.items():
            if column in self.data.columns and values:
                filtered_data = filtered_data[filtered_data[column].isin(values)]

        # Apply date range filters
        if date_range_filters:
            for column, (start_date, end_date) in date_range_filters.items():
                if column in self.data.columns and pd.api.types.is_datetime64_any_dtype(self.data[column]):
                    if start_date and end_date:
                        filtered_data = filtered_data[
                            (filtered_data[column] >= start_date) &
                            (filtered_data[column] <= end_date)
                            ]
                    elif start_date:
                        filtered_data = filtered_data[filtered_data[column] >= start_date]
                    elif end_date:
                        filtered_data = filtered_data[filtered_data[column] <= end_date]

        return filtered_data

    def get_metrics(self):
        return self.metrics

    def get_dimensions(self):
        return self.dimensions

    def get_date_columns(self):
        return self.date_columns

    def get_unique_values(self, column):
        if column in self.data.columns:
            if pd.api.types.is_datetime64_any_dtype(self.data[column]):
                # For date columns, return min and max dates
                return sorted(self.data[column].unique())
            else:
                # For other columns, return sorted unique values
                return sorted(self.data[column].unique().tolist())
        return []

    def get_date_range(self, column):
        """Get the minimum and maximum dates in a date column"""
        if column in self.data.columns and pd.api.types.is_datetime64_any_dtype(self.data[column]):
            min_date = self.data[column].min()
            max_date = self.data[column].max()
            return min_date, max_date
        return None, None

    def get_metric_type(self, metric):
        """Get the type of a metric (currency, percentage, or number)"""
        return self.metric_types.get(metric, 'number')

    def get_aggregation_type(self, metric):
        """Get how a metric should be aggregated (sum or average)"""
        return self.aggregation_types.get(metric, 'sum')

    def get_formatted_label(self, metric):
        """Get a formatted label for a metric based on its type"""
        metric_type = self.get_metric_type(metric)

        if metric_type == 'currency':
            return f"£ {metric}"
        elif metric_type == 'percentage':
            return f"{metric} (%)"
        else:
            return metric

    def aggregate_metric(self, data, metric, group_columns=None):
        """Aggregate a metric using the appropriate method (sum or average)"""
        aggregation_type = self.get_aggregation_type(metric)

        if group_columns:
            if aggregation_type == 'average':
                return data.groupby(group_columns)[metric].mean().reset_index()
            else:
                return data.groupby(group_columns)[metric].sum().reset_index()
        else:
            if aggregation_type == 'average':
                return data[metric].mean()
            else:
                return data[metric].sum()