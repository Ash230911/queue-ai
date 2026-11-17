"""Allocation strategies (member 2). Add a new strategy by subclassing Strategy and registering it.

Hooks used by sim.engine:
  route(st, cust)  dedicated strategies: index of the counter whose own queue the customer joins
  pick(st)         pooled strategies: index into st.pool of the customer served next
  open_flex(st)    called before dispatch: open flex counters when needed
  close_flex(st)   called after dispatch: close idle flex counters
"""


class Strategy:
    key = ""
    name = ""
    description = ""
    dedicated = False  # True: one queue per counter. False: one shared queue.
    priority = False   # True: priority customers are served first
    uses_flex = False  # True: params.flex extra counters may be opened

    def reset(self):
        pass

    def route(self, st, cust):
        raise NotImplementedError

    def pick(self, st):
        return 0

    def open_flex(self, st):
        pass

    def close_flex(self, st):
        pass


class RoundRobin(Strategy):
    key = "baseline"
    name = "Baseline: one queue per counter"
    description = "Customers are assigned to counters in rotation and cannot switch queues."
    dedicated = True

    def reset(self):
        self._i = 0

    def route(self, st, cust):
        b = self._i % len(st.counters)
        self._i += 1
        return b


class JoinShortestQueue(Strategy):
    key = "jsq"
    name = "Join shortest queue"
    description = "Each arrival joins the counter with the fewest people (waiting plus in service)."
    dedicated = True

    def route(self, st, cust):
        load = lambda c: len(c.queue) + (1 if c.cur else 0)
        return min(range(len(st.counters)), key=lambda i: (load(st.counters[i]), i))


class SharedQueue(Strategy):
    key = "shared"
    name = "Single shared queue"
    description = "One first-come-first-served line feeding whichever counter frees up first."


class PriorityFlex(SharedQueue):
    key = "priority_flex"
    name = "Shared queue + priority + flex staff"
    description = "Shared queue, priority customers served first, and flex staff open extra counters when the line builds."
    priority = True
    uses_flex = True

    def pick(self, st):
        for i, x in enumerate(st.pool):
            if x.pri:
                return i
        return 0

    def _flex(self, st):
        return [c for c in st.counters if c.id >= st.params.c]

    def open_flex(self, st):
        flex = self._flex(st)
        opened = sum(1 for c in flex if c.open)
        for c in flex:
            if not c.open and len(st.pool) >= st.params.c * (opened + 1):
                c.open, c.since = True, st.t
                opened += 1

    def close_flex(self, st):
        if st.pool:
            return
        for c in self._flex(st):
            if c.open and c.cur is None:
                c.open = False
                c.open_time += st.t - c.since


STRATEGIES = {cls.key: cls for cls in (RoundRobin, JoinShortestQueue, SharedQueue, PriorityFlex)}


def get_strategy(key: str) -> Strategy:
    if key not in STRATEGIES:
        raise KeyError(f"Unknown strategy '{key}'. Available: {', '.join(STRATEGIES)}")
    s = STRATEGIES[key]()
    s.reset()
    return s
