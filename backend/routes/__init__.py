# Pacote routes: exporta os blueprints para o app.py registrar.
from routes.clientes import bp as clientes_bp
from routes.produtos import bp as produtos_bp
from routes.pedidos import bp as pedidos_bp

__all__ = ["clientes_bp", "produtos_bp", "pedidos_bp"]
