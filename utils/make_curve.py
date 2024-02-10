#!/bin/python3

file = open("curve.txt", "w")

b8 = 1.89
b25 = 1.94

for i in range(0, 800, 100):
    file.write(str(i * 1.89 / 800) + " " + str(i) + "\n")

for i in range(800, 2500, 100):
    file.write(str(b8 + (i - 800) * (b25 - b8) / 1700) + " " + str(i) + "\n")

file.close()