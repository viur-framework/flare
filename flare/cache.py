"""The cache module is set on top of the network module and caches any entries read.

When the same entry (identified by module and key) is requested, it first is returned
from the cache, when already there.
"""

from .network import NetworkService, DeferredCall, NiceError


class Cache(object):
    def __init__(self):
        super(Cache, self).__init__()
        self.cache = {}
        self.compound = {}
        self.structure = {}
        self.plans = {}

        NetworkService.registerChangeListener(self)

    def updateStructure(self, module, structure):
        if isinstance(structure, list):
            structure = {k: v for k, v in structure}

            for struct in structure.values():
                if "values" in struct.keys() and isinstance(struct["values"], list):
                    struct["values"] = {k: v for k, v in struct["values"]}

        self.structure[module] = structure
        return self.structure[module]

    def update(self, module, key, data, structure=None):
        if module not in self.cache:
            self.cache[module] = {}

        self.cache[module][key] = data

        if structure:
            self.updateStructure(module, structure)

        return data

    def lookup(self, module, key="current"):
        if module in self.cache:
            return self.cache[module].get(key)

        return None

    def struct(self, module):
        if module in self.structure:
            return self.structure.get(module)

        return None

    def start(self, plan, finishHandler=None, failureHandler=None):
        assert isinstance(plan, Plan)
        assert plan not in self.plans
        self.plans[plan] = {
            "finishHandler": finishHandler,
            "failureHandler": failureHandler,
        }

        plan.run(self)

    def finish(self, plan):
        assert isinstance(plan, Plan)
        assert plan in self.plans

        finishHandler = self.plans[plan]["finishHandler"]

        ret = {}
        while plan:
            ret[plan.module] = plan.result
            plan = plan.follow

        if plan:
            del self.plans[plan]

        if callable(finishHandler):
            finishHandler(ret)

    def require(self, *args):
        ret = []

        for arg in args:
            if isinstance(arg, tuple) and len(arg) == 2:
                module = arg[0]
                key = arg[1]
            else:
                module = arg
                key = "current"

            data = self.lookup(module, key)
            # assert data, "No cached entry for '%s' with key '%s'" % (module, key)
            ret.append(data)

        return ret if len(ret) > 1 else ret[0]

    def invalidate(self, *args):
        if not args:
            print("Invalidating entire cache")
            self.cache.clear()
            self.compound.clear()
            return

        for module in args:
            print("Invalidating %r" % module)

            if module in self.cache:
                del self.cache[module]

            if module in self.compound:
                del self.compound[module]

    def onDataChanged(self, module, key=None, **kwargs):
        if module in self.cache:
            if key:
                # Invalidate direct entry
                if key in self.cache[module]:
                    del self.cache[module][key]
                    print("entry '%s' removed from %s" % (key, module))

                # Invalidate all compound results on the module
                if module in self.compound:
                    del self.compound[module]
                    print("compound results for %s cleared" % module)
            else:
                # Invalidate entire module
                self.invalidate(module)
                print("module %s entirely invalidated" % module)

    def request(self, *args, finishHandler=None, failureHandler=None):
        last = start = None

        for arg in args:
            if isinstance(arg, dict):
                plan = Plan(**arg)
            else:
                assert isinstance(arg, Plan)
                plan = arg

            if last:
                last.follow = plan

            last = plan
            if start is None:
                start = plan

        self.start(start, finishHandler=finishHandler, failureHandler=failureHandler)


class Plan(object):
    def __init__(
        self, module, action, params=None, follow=None, alias="current", local=True
    ):
        super(Plan, self).__init__()

        if module.startswith("!"):
            module = module[1:]
            self.optional = True
        else:
            self.optional = False

        self.parent = None
        self.module = module

        assert action in ["view", "list"]
        self.action = action
        self.alias = alias

        self.result = None

        if isinstance(params, list):
            if all([isinstance(key, str) for key in params]):
                self.params = [{"key": key} for key in params]
            else:
                self.params = params

        elif isinstance(params, str):
            self.params = {"key": params}

        else:
            assert isinstance(
                params or {}, dict
            ), "Either give me a string, a dict, a list of strings or a list of dict"
            self.params = params or {}

        # print("Plan", self.module, self.action, self.params)

        if follow is not None:
            assert isinstance(follow, Plan)
            follow.parent = self

        self.follow = follow

    def run(self, cache):
        assert isinstance(cache, Cache)

        if isinstance(self.params, list):
            if self.params:
                cparams = self.params.pop(0)
            else:
                return True

        else:
            cparams = self.params

        def fetchFromCache(params):
            if self.action == "view" and len(params.keys()) == 1 and "key" in params:
                data = cache.lookup(self.module, params["key"])
                if data:
                    if isinstance(self.params, list):
                        if self.result is None:
                            self.result = []

                        self.result.append(data)
                    else:
                        self.result = data

                    if self.alias:
                        cache.update(self.module, self.alias, data)

                    self.finish(cache)
                    return True

        # Try to fetch from cache with original params
        if fetchFromCache(cparams):
            return True

        # Involve parameters from parent results
        params = {}
        for key, val in cparams.items():
            if ":" in str(val):
                mod, field = val.split(":", 1)

                parent = self.parent
                data = None
                while parent:
                    if parent.alias and parent.module == mod:
                        data = cache.lookup(parent.module, parent.alias)
                        break

                    parent = parent.parent

                if parent is None:
                    raise KeyError(
                        "No previously handled module '%s' in current plan found" % mod
                    )
                if data is None:
                    raise ValueError(
                        "The latest value of module '%s' could not be found" % mod
                    )

                for part in field.split("."):
                    data = data[part]

                    if data is None:
                        if self.optional:
                            self.finish(cache)
                            return True

                        raise ValueError(
                            "Field '%s' cannot be retrieved for module '%s' "
                            "(make this module optional to avoid this problem!)"
                            % field,
                            self.module,
                        )

                params[key] = data

            else:
                params[key] = val

        # Try to fetch from cache
        if fetchFromCache(params):
            return True

        # Check for cached compound list results
        if self.action == "list":
            compoundKey = "&".join(
                [
                    ("%s=%s" % (str(key), str(params[key])))
                    for key in sorted(params.keys())
                    if key not in ["cursor", "amount"]
                ]
            )
            print("compound check", self.module, compoundKey)

            if (
                self.module in cache.compound
                and compoundKey in cache.compound[self.module]
            ):
                if (
                    cache.compound[self.module][compoundKey] is None
                ):  # Check if under construction?
                    print("under construction", self.module, compoundKey)
                    DeferredCall(self.run, cache, _delay=125)
                    return

                self.result = cache.compound[self.module][compoundKey]
                self.finish(cache)
                return True

            if self.module not in cache.compound:
                cache.compound[self.module] = {}

            cache.compound[self.module][
                compoundKey
            ] = None  # Mark for under construction!

            if "amount" not in params:
                params["amount"] = 99

        # New request required

        # print("---")
        # print(self.module)
        # print(self.action)
        # print(params)

        req = NetworkService.request(
            self.module,
            self.action,
            params=params,
            successHandler=self._onRequestSuccess,
            failureHandler=self._onRequestFailure,
            kickoff=False,
        )
        req.cache = cache
        req.params = params

        req.kickoff()

        return req

    def finish(self, cache):
        if isinstance(self.params, list) and self.params:
            self.run(cache)
            return

        if self.follow:
            self.follow.run(cache)
        else:
            root = self
            while root.parent:
                root = root.parent

            cache.finish(root)

    def _onRequestSuccess(self, req):
        answ = NetworkService.decode(req)
        assert "action" in answ

        if answ["action"] == self.action:
            if self.action == "view":

                assert "values" in answ
                values = req.cache.update(
                    self.module,
                    answ["values"]["key"],
                    answ["values"],
                    answ["structure"],
                )

                if isinstance(self.params, list):
                    if self.result is None:
                        self.result = [values]
                    else:
                        self.result.append(values)

                else:
                    self.result = values

                if self.alias:
                    req.cache.update(self.module, self.alias, values)

                self.finish(req.cache)

            elif self.action == "list":
                assert "skellist" in answ

                if answ["skellist"]:
                    for skel in answ["skellist"]:
                        req.cache.update(
                            self.module, skel["key"], skel, answ["structure"]
                        )

                        if self.alias and skel is answ["skellist"][-1]:
                            req.cache.update(self.module, self.alias, skel)

                    if self.result is None:
                        self.result = answ["skellist"]
                    else:
                        self.result.extend(answ["skellist"])

                    if (
                        "search" not in req.params
                        and answ["cursor"]
                        and len(answ["skellist"])
                        == req.params.get("amount", len(answ["skellist"]))
                    ):
                        req.params["cursor"] = answ["cursor"]
                        nreq = NetworkService.request(
                            self.module,
                            self.action,
                            params=req.params,
                            successHandler=self._onRequestSuccess,
                            failureHandler=self._onRequestFailure,
                            kickoff=False,
                        )
                        nreq.cache = req.cache
                        nreq.params = req.params
                        nreq.kickoff()
                        return

                elif self.result is None:
                    self.result = []

                # Cache compound resultsets
                compoundKey = "&".join(
                    [
                        ("%s=%s" % (str(key), str(req.params[key])))
                        for key in sorted(req.params.keys())
                        if key not in ["cursor", "amount"]
                    ]
                )

                print("compound create", self.module, compoundKey, len(self.result))

                req.cache.compound[self.module][compoundKey] = self.result

                self.finish(req.cache)

    def _onRequestFailure(self, req, code):
        if not self.optional:
            if len(req.params) == 1 and "key" in req.params:
                params = "key=%s" % req.params["key"]
            else:
                params = str(req.params)

            NiceError(req, code, params)

        self.finish(req.cache)
