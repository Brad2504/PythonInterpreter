from pyinterp.lexer import Lexer as lexer
import numpy as np

def fact(x):
    if x == 0:
        return 1
    else:
        return x * fact(x - 1)

class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

print(fact(5))

x = 0

for i in range(10):
    x += i

print(x)

x = "print('hello')"

print(lexer(x).tokenize())

rectangle = Rectangle(3, 4)
print(rectangle.area())

nums = np.array([1, 2, 3])
print(np.sum(nums))