class Foo:
    def vals(self):
        for x in ["a", "b", "z"]:
            yield from self._special(x)

    def _special(self, x):
        if x == "b":
            yield "b1"
            yield "b2"
        else:
            yield x

myf = Foo()
for x in myf.vals():
    print(x)
