"""Truth-independent budget-curve arithmetic for FSG4."""
from __future__ import annotations
import numpy as np


def pad_curve(c: list[float], n: int) -> list[float]:
    if not c:
        raise ValueError("empty coverage curve")
    if len(c) > n:
        raise ValueError("curve longer than budget")
    return [float(x) for x in c] + [float(c[-1])] * (n-len(c))


def normalized_auc(c: list[float]) -> float:
    a=np.asarray(c,float)
    if len(a)==0:
        raise ValueError("empty coverage curve")
    if len(a)==1:
        return float(a[0])
    return float(np.sum((a[:-1]+a[1:])*0.5)/(len(a)-1))


def self_test() -> None:
    active=[.40,.60,.80,.98,1.0];scan=[.40,.40,.60,.60,.80]
    gain=normalized_auc(active)-normalized_auc(scan)
    if gain <= .10:
        raise AssertionError("known active curve must have >10 pp AUC gain")
    if pad_curve([.4,.7,.95],5) != [.4,.7,.95,.95,.95]:
        raise AssertionError("early-stop coverage padding wrong")
    print(f"[fsg4-metrics] PASS known_auc_gain={gain:.6f} early_stop_padding=true")

if __name__=='__main__':self_test()
