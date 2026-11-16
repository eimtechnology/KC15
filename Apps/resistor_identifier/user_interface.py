"""Widget geometry and band values for the 240 x 240 resistor tool."""

_WHITE = 0xffff
_MINT = 0xb7f9  # Pale green in RGB565


class _Box:
    def __init__(self, x_pos, y_pos, width, height, color, border_thickness):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.width = width
        self.height = height
        self.color = color
        # The renderer paints the outer rectangle, then this inset rectangle.
        self.border_x = x_pos + border_thickness
        self.border_y = y_pos + border_thickness
        self.border_width = width - 2 * border_thickness
        self.border_height = height - 2 * border_thickness
        self.fill_color = _WHITE

    def is_highlighted(self, active):
        self.fill_color = _MINT if active else _WHITE


class Option_Box(_Box):
    fourth_band_values = (
        'x1', 'x10', 'x100', 'x1K', 'x10K', 'x100K',
        'x1M', 'x10M', 'x100M', 'x1G', 'x0.1', 'x0.01',
    )
    multiplier_values = (
        1, 10, 100, 1000, 10000, 100000,
        1000000, 10000000, 100000000, 1000000000, 0.1, 0.01,
    )
    # The reference photo puts 5% under silver. Use the resistor values here.
    fifth_band_values = (
        '', '1%', '2%', '', '', '0.5%',
        '0.25%', '0.10%', '0.05%', '', '5%', '10%',
    )

    def __init__(self, x_pos, y_pos, color, border_thickness, box_id):
        super().__init__(x_pos, y_pos, 60, 35, color, border_thickness)
        self.id = box_id


class Band_Selector(_Box):
    def __init__(self, x_pos, y_pos, border_thickness):
        super().__init__(x_pos, y_pos, 240, 40, 0xe71c, border_thickness)

