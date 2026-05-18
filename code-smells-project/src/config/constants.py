"""Domain constants. Moved out of inline literals in routes/controllers."""

PRODUTO_NOME_MIN_LEN = 2
PRODUTO_NOME_MAX_LEN = 200
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_DEFAULT = "geral"

PEDIDO_STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
PEDIDO_STATUS_DEFAULT = "pendente"

DISCOUNT_TIERS = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)

USUARIO_TIPO_DEFAULT = "cliente"
