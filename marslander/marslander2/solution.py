import sys
import math

surface_n = int(input())  # the number of points used to draw the surface of Mars.
#print('{}'.format(surface_n), file=sys.stderr)
for i in range(surface_n):
    land_x, land_y = [int(j) for j in input().split()]
    #print('{} {}'.format(land_x, land_y), file=sys.stderr)

while True:
    x, y, h_speed, v_speed, fuel, rotate, power = [int(i) for i in input().split()]
    print('{} {} {} {} {} {} {}'.format(x, y, h_speed, v_speed, fuel, rotate, power), file=sys.stderr)

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    print("0 0")# rotate power