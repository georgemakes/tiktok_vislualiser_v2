class TikTokStyle:
    def __init__(self):
        # Basic colors and styling
        self.background_color = "#000000"
        self.text_color = "#ffffff"
        self.grid_color = "#333333"
        self.line_color = "#00f2ea"  # TikTok blue/teal color
        self.font_family = "Arial, sans-serif"
        self.title_font_size = 16
        self.text_font_size = 12
        self.line_width = 3
        self.axis_line_width = 1

        # Chart-specific styling
        self.colorscale = "viridis"  # For heatmap
        self.bar_colors = ["#00f2ea", "#ff0050", "#ccff00", "#ee1d52", "#69c9d0"]  # TikTok colors
        self.marker_size = 8  # Marker size for line charts

        # Custom color sequence for grouped data
        self.color_sequence = ["#00f2ea", "#ff0050", "#ccff00", "#ee1d52", "#69c9d0"]

        # Line chart specific options
        self.show_markers = True  # Whether to show data points on line charts
        self.line_shape = "linear"  # Can be: 'linear', 'spline', 'hv', 'vh', 'hvh', 'vhv'

        # General chart options
        self.hide_zero_values = False  # Whether to hide zero values in charts

    def get_layout_params(self):
        return {
            "plot_bgcolor": self.background_color,
            "paper_bgcolor": self.background_color,
            "font": dict(
                family=self.font_family,
                size=self.text_font_size,
                color=self.text_color
            ),
            "title": {
                "font": dict(size=self.title_font_size, color=self.text_color),
                "x": 0.5,
                "xanchor": "center"
            },
            "xaxis": dict(
                gridcolor=self.grid_color,
                showline=True,
                linecolor=self.text_color,  # Use text color for axis lines
                linewidth=self.axis_line_width,
                tickfont=dict(color=self.text_color),
                title=dict(font=dict(color=self.text_color))
            ),
            "yaxis": dict(
                gridcolor=self.grid_color,
                showline=True,
                linecolor=self.text_color,  # Use text color for axis lines
                linewidth=self.axis_line_width,
                tickfont=dict(color=self.text_color),
                title=dict(font=dict(color=self.text_color))
            ),
            "legend": dict(
                bgcolor=self.background_color,
                font=dict(color=self.text_color),
                title=dict(font=dict(color=self.text_color))
            ),
            "colorway": self.color_sequence  # Set color sequence for all traces
        }

    def get_line_params(self):
        return dict(
            width=self.line_width,
            color=self.line_color,
            shape=self.line_shape  # Apply line shape (linear or spline)
        )

    def get_marker_params(self):
        if self.show_markers:
            return dict(size=self.marker_size)
        else:
            return dict(size=0)  # Set size to 0 to hide markers

    def get_coloraxis_params(self):
        return dict(
            colorscale=self.colorscale,
            colorbar=dict(
                title=dict(text="Value", font=dict(color=self.text_color)),
                tickfont=dict(color=self.text_color)
            )
        )

    def get_bar_params(self):
        return {
            "barmode": "group",
            "colorway": self.bar_colors
        }

    def to_dict(self):
        """Convert style settings to dictionary for saving as preferences"""
        return {
            "background_color": self.background_color,
            "text_color": self.text_color,
            "grid_color": self.grid_color,
            "line_color": self.line_color,
            "font_family": self.font_family,
            "title_font_size": self.title_font_size,
            "text_font_size": self.text_font_size,
            "line_width": self.line_width,
            "axis_line_width": self.axis_line_width,
            "colorscale": self.colorscale,
            "bar_colors": self.bar_colors,
            "marker_size": self.marker_size,
            "color_sequence": self.color_sequence,
            "show_markers": self.show_markers,
            "line_shape": self.line_shape,
            "hide_zero_values": self.hide_zero_values
        }

    @classmethod
    def from_dict(cls, style_dict):
        """Create style instance from dictionary"""
        style = cls()
        for key, value in style_dict.items():
            if hasattr(style, key):
                setattr(style, key, value)
        return style