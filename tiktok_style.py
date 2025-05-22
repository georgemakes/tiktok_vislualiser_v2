class TikTokStyle:
    def __init__(self):
        # Basic colors and styling
        self.background_color = "#000000"
        self.text_color = "#ffffff"
        self.grid_color = "#333333"
        self.line_color = "#2a6bfd"  # Fixed: removed 'ff' suffix
        self.font_family = "Arial, sans-serif"
        self.title_font_size = 16
        self.text_font_size = 12
        self.line_width = 3
        self.axis_line_width = 1

        # Chart-specific styling
        self.colorscale = "viridis"  # For heatmap

        # Fixed color palette - removed invalid colors
        self.bar_colors = [
            "#fe2c56",  # Red/Pink
            "#2a6bfd",  # Blue (fixed)
            "#f4f004",  # Yellow
            "#00faa2",  # Green
            "#ff6b35",  # Orange
            "#9b59b6",  # Purple
            "#1abc9c",  # Teal
            "#e74c3c",  # Red
            "#f39c12",  # Dark Orange
            "#34495e",  # Dark Blue-Gray
            "#8e44ad",  # Dark Purple
            "#16a085",  # Dark Teal
            "#2ecc71",  # Emerald Green
            "#3498db",  # Sky Blue
            "#e67e22",  # Carrot Orange
            "#95a5a6",  # Gray
            "#d35400",  # Pumpkin
            "#27ae60",  # Nephritis Green
            "#2980b9",  # Belize Blue
            "#c0392b"   # Dark Red
        ]

        # Use the same colors for line charts
        self.color_sequence = [
            "#fe2c56",  # Red/Pink
            "#2a6bfd",  # Blue (fixed)
            "#f4f004",  # Yellow
            "#00faa2",  # Green
            "#ff6b35",  # Orange
            "#9b59b6",  # Purple
            "#1abc9c",  # Teal
            "#e74c3c",  # Red
            "#f39c12",  # Dark Orange
            "#34495e",  # Dark Blue-Gray
            "#8e44ad",  # Dark Purple
            "#16a085",  # Dark Teal
            "#2ecc71",  # Emerald Green
            "#3498db",  # Sky Blue
            "#e67e22",  # Carrot Orange
            "#95a5a6",  # Gray
            "#d35400",  # Pumpkin
            "#27ae60",  # Nephritis Green
            "#2980b9",  # Belize Blue
            "#c0392b"   # Dark Red
        ]

        self.marker_size = 8
        self.show_markers = True
        self.line_shape = "linear"
        self.hide_zero_values = False

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
                linecolor=self.text_color,
                linewidth=self.axis_line_width,
                tickfont=dict(color=self.text_color),
                title=dict(font=dict(color=self.text_color))
            ),
            "yaxis": dict(
                gridcolor=self.grid_color,
                showline=True,
                linecolor=self.text_color,
                linewidth=self.axis_line_width,
                tickfont=dict(color=self.text_color),
                title=dict(font=dict(color=self.text_color))
            ),
            "legend": dict(
                bgcolor=self.background_color,
                font=dict(color=self.text_color),
                title=dict(font=dict(color=self.text_color))
            ),
            "colorway": self.color_sequence
        }

    def get_line_params(self):
        return dict(
            width=self.line_width,
            color=self.line_color,
            shape=self.line_shape
        )

    def get_marker_params(self):
        if self.show_markers:
            return dict(size=self.marker_size)
        else:
            return dict(size=0)

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
        style = cls()
        for key, value in style_dict.items():
            if hasattr(style, key):
                setattr(style, key, value)
        return style