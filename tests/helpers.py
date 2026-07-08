from verdict.receipts import Receipt, Gated
from verdict.gate import sign


def gated(value, **kw):
    r = Receipt(value=value, source_dataset="Zhu2025", source_file="de.h5ad",
                computation="test", query="test", **kw)
    return Gated(value=value, receipt=sign(r))
