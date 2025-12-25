"""Script simples para monitorar preços de criptomoedas via CoinGecko.

O script limpa o terminal, obtém a hora atual e exibe os preços de
Bitcoin (BTC) e Ethereum (ETH) em dólares.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen


COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
)


def limpar_terminal() -> None:
    """Limpa o terminal em sistemas Unix e Windows."""

    comando = "cls" if os.name == "nt" else "clear"
    os.system(comando)


def buscar_precos() -> dict[str, float]:
    """Busca os preços atuais de BTC e ETH em USD.

    Returns:
        dict[str, float]: Um dicionário com as chaves "BTC" e "ETH".
    """

    request = Request(COINGECKO_URL, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except URLError as exc:  # pragma: no cover - caso de rede
        raise SystemExit(f"Erro ao acessar a API: {exc}") from exc

    try:
        return {
            "BTC": float(data["bitcoin"]["usd"]),
            "ETH": float(data["ethereum"]["usd"]),
        }
    except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - dados inesperados
        raise SystemExit("Resposta inesperada da API.") from exc


def formatar_preco(valor: float) -> str:
    """Formata um preço para exibição."""

    return f"${valor:,.2f}"


def main() -> None:
    limpar_terminal()
    horario = datetime.now(timezone.utc).astimezone()
    precos = buscar_precos()

    print("🚀 Monitor de Criptomoedas")
    print("-" * 30)
    print(f"⏰ Atualizado em: {horario:%d/%m/%Y %H:%M:%S %Z}")
    print()
    print("Moeda  | Preço (USD)")
    print("--------------------")
    print(f"BTC    | {formatar_preco(precos['BTC'])}")
    print(f"ETH    | {formatar_preco(precos['ETH'])}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
