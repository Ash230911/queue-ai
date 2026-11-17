"""Queueing theory reference values (member 3)."""


def erlang_c(c: int, a: float):
    """Probability an arrival must wait in an M/M/c queue. a = offered load (lambda * E[S]). None if unstable."""
    if a >= c:
        return None
    s, t = 0.0, 1.0
    for k in range(c):
        if k:
            t *= a / k
        s += t
    top = t * a / c * c / (c - a)
    return top / (s + top)


def mmc(c: int, lam_per_min: float, mean_service: float):
    a = lam_per_min * mean_service
    pw = erlang_c(c, a)
    if pw is None:
        return {"stable": False, "offered_load": a, "rho": a / c}
    mu = 1.0 / mean_service
    wq = pw / (c * mu - lam_per_min)
    return {"stable": True, "offered_load": a, "rho": a / c, "p_wait": pw, "wq": wq, "lq": wq * lam_per_min}
