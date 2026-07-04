# assets/styles.py

COLORS = {
    "bg": "#121214",             # Negro mate profundo / Dark Charcoal (Fondo general)
    "card": "#1A1A1E",           # Gris oscuro suave para las tarjetas (hace que floten sobre el fondo)
    "text": "#F5F5F7",           # Blanco premium / Off-white (Máxima legibilidad)
    "muted": "#A1A1AA",          # Gris claro apagado para subtítulos y x1, x2...
    "primary": "#E8A0B5",        # Rosa pastel / Blush (Resalta hermoso sobre el oscuro)
    "primary_hover": "#D4899E",  # Hover del botón principal
    "secondary": "#C8A2C8",      # Lila pastel más encendido para que no se pierda en lo oscuro
    "secondary_hover": "#A9849D",# Hover para secundarios
    "border": "#2D2D34",         # Gris oscuro sutil para bordes (así las cajas no se ven toscas)
    "footer_text": "#6B6B76"     # Gris oscuro sutil para los créditos inferiores
}

FONTS = {
    "title": ("Century Gothic", 24, "bold"),
    "subtitle": ("Segoe UI", 13),
    "section": ("Century Gothic", 15, "bold"),
    "body_bold": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 13),
    "caption": ("Segoe UI", 12),           # Corregido: Para descripciones y subtítulos pequeños
    "table": ("Segoe UI", 12, "bold"),      # Corregido: Para las matrices matemáticas de Simplex y 2 Fases
    "footer": ("Segoe UI", 11, "italic")
}

PADDING = {
    "xs": 4,
    "sm": 8,
    "md": 15,
    "lg": 22,
    "xl": 30
}