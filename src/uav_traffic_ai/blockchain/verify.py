from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import requests


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    found_payloads: List[bytes]
    opreturn_hexes: List[str]


def _parse_pushdatas_from_opreturn_script_hex(script_hex: str) -> List[bytes]:
    """
    Script típico WoC opreturn: "006a <pushdata...>" (OP_FALSE OP_RETURN).
    Implementación simple para PUSHDATA (len byte) + OP_PUSHDATA1.
    """
    b = bytes.fromhex(script_hex)
    if len(b) < 2:
        return []
    # acepta 0x6a directamente o 0x00 0x6a
    i = 0
    if b[0] == 0x00 and len(b) >= 2 and b[1] == 0x6A:
        i = 2
    elif b[0] == 0x6A:
        i = 1
    else:
        return []

    out: List[bytes] = []
    while i < len(b):
        op = b[i]
        i += 1

        if op == 0x4C:  # OP_PUSHDATA1
            if i >= len(b):
                break
            ln = b[i]
            i += 1
            out.append(b[i : i + ln])
            i += ln
        elif 1 <= op <= 75:
            ln = op
            out.append(b[i : i + ln])
            i += ln
        else:
            # opcode raro: cortamos
            break
    return out


def verify_sha256_in_tx_opreturn(
    *,
    woc_base: str,
    chain_name: str,
    txid: str,
    expected_sha256_hex: str,
) -> VerifyResult:
    """
    WhatsOnChain endpoint:
    GET https://api.whatsonchain.com/v1/bsv/<network>/tx/<txid>/opreturn :contentReference[oaicite:3]{index=3}
    """
    network = "test" if chain_name == "test" else "main"
    url = f"{woc_base}/v1/bsv/{network}/tx/{txid}/opreturn"

    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()  # [{ "n": int, "hex": "..." }, ...]

    op_hexes: List[str] = [str(x.get("hex", "")) for x in data if "hex" in x]
    payloads: List[bytes] = []
    for h in op_hexes:
        payloads.extend(_parse_pushdatas_from_opreturn_script_hex(h))

    # Buscamos el hash como ASCII dentro de pushdatas
    ok = any(expected_sha256_hex.encode("utf-8") in p for p in payloads)
    return VerifyResult(ok=ok, found_payloads=payloads, opreturn_hexes=op_hexes)
