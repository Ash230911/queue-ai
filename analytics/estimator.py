"""Waiting-time estimator quoted to a customer on arrival (member 3).

Uses only information known at arrival time: queue contents, residual service time of
customers in service, and the historical mean service time (st.mean_service).
Extend: use service-type-specific means, or train a regression model on logged data.
"""


def estimate_wait(st, cust, strategy, counter=None) -> float:
    if strategy.dedicated:
        c = st.counters[counter]
        return len(c.queue) * st.mean_service + (max(0.0, c.end - st.t) if c.cur else 0.0)
    open_ = [c for c in st.counters if c.open]
    if not st.pool and any(c.cur is None for c in open_):
        return 0.0
    ahead = sum(1 for y in st.pool if y.pri) if (strategy.priority and cust.pri) else len(st.pool)
    resid = sum(max(0.0, c.end - st.t) for c in open_ if c.cur)
    return (ahead * st.mean_service + resid) / len(open_)
