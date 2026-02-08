from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from bsvlib import Wallet
from bsvlib.constants import Chain
from bsvlib.keys import Key


@dataclass(frozen=True)
class AnchorResult:
    txid: str
    raw_response: str


def _chain_from_name(name: str) -> Chain:
    return Chain.TEST if name == "test" else Chain.MAIN


def anchor_sha256_opreturn(
    *,
    chain_name: str,
    wif: str,
    dust_sats: int,
    scene_id: str,
    sha256_hex: str,
    model: str,
    created_at_utc: datetime,
) -> AnchorResult:
    """
    Crea y emite una tx con OP_RETURN usando bsvlib (pushdatas).
    Ejemplo de OP_RETURN en bsvlib: create_transaction(..., pushdatas=[...]). :contentReference[oaicite:2]{index=2}
    """
    if not wif:
        raise ValueError("Falta BSV_WIF_TESTNET en .env (necesitas testnet coins).")

    chain = _chain_from_name(chain_name)
    key = Key(wif)
    change_addr = key.address()
    
    if chain == Chain.TEST and not change_addr.startswith(("m", "n", "2")):
        raise ValueError(
            f"WIF no parece testnet. Dirección derivada: {change_addr}. "
            "En testnet suele empezar por m/n (o 2 si es P2SH)."
        )

    # Output “dust” a tu propia dirección + OP_RETURN (pushdatas).
    outputs = [(change_addr, int(dust_sats))]

    # Todo debe ser corto (pushdata < 75 bytes ideal).
    # Guardamos campos auditables:
    # - prefix + version
    # - scene_id
    # - sha256
    # - timestamp
    # - model
    prefix = "UAVTAIVD_V1"
    ts = created_at_utc.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    pushdatas: List[object] = [prefix, scene_id, sha256_hex, ts, model]

    wallet = Wallet([wif], chain=chain)
    tx = wallet.create_transaction(outputs=outputs, pushdatas=pushdatas)
    resp = tx.broadcast()

    # Resp puede ser un objeto; intentamos extraer txid de forma robusta.
    txid = getattr(resp, "data", None) or getattr(resp, "txid", None) or getattr(resp, "tx_id", None) or str(resp)

    return AnchorResult(txid=str(txid), raw_response=str(resp))
