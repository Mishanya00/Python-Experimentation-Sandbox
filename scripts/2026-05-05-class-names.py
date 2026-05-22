class Base:
    def __init__(self):
        self.class_name = self.__class__.__name__


class Descendant(Base):
    def __init__(self):
        super().__init__()


a = Base()
b = Descendant()

print(a.class_name)
print(b.class_name)