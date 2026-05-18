"""Sales report orchestration. Discount tiers moved out of the data layer."""
from src.config.constants import DISCOUNT_TIERS
from src.models import pedido_model


def _calcular_desconto(faturamento):
    for limite, taxa in DISCOUNT_TIERS:
        if faturamento > limite:
            return faturamento * taxa
    return 0.0


def vendas():
    agg = pedido_model.aggregate_for_report()
    faturamento = agg["faturamento"] or 0
    total_pedidos = agg["total_pedidos"]
    desconto = _calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": agg["pendentes"],
        "pedidos_aprovados": agg["aprovados"],
        "pedidos_cancelados": agg["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
