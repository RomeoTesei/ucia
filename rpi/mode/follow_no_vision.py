import cv2 as cv

from rosa import Rosa

# ROMEO : For this file, I just have one question. This also applies to the part in follow_vision.py/combined_follow_line because the code is the same.
# Why implement this version of a line following algorithm using the sensors, and not copy the classic behaviour of the Thymio ?
# You created an algorithm a little bit too smart compared to the Thymio, which can be confusing when comparing it to the ones with vision during the sessions.
# What I mean by that, is that the current light blue mode, using this code, can do things that the original line following mode of the Thymio can't, when they're supposed to be the same.

import time

base_speed = 0.1
turn_ratio = 0.9
THRESHOLD_DIFFERENCE = 50
following_left_edge = True

def set_speed(rosa, ls, rs):
    rosa.left_wheel.speed = ls
    rosa.right_wheel.speed = rs

def set_straight(rosa):
    set_speed(rosa, base_speed, base_speed)

def set_right(rosa):
    left_wheel_speed = base_speed * (1 + turn_ratio)
    right_wheel_speed = base_speed * (1 - turn_ratio)

    set_speed(rosa,left_wheel_speed, right_wheel_speed)

def set_left(rosa):
    left_wheel_speed = base_speed * (1 - turn_ratio)
    right_wheel_speed = base_speed * (1 + turn_ratio)
    
    set_speed(rosa,left_wheel_speed, right_wheel_speed)

def follow_line_as_Thymio(rosa, reflected):
    left_sensor = reflected[0]
    right_sensor = reflected[1]
    
    # ROMEO : I don't know the range of the reflected values, so these are temporary and arbitrary.
    black_threshold = 50
    white_threshold = 200
    
    if left_sensor < black_threshold and right_sensor < black_threshold: # Both sensors see black -> move forward
        set_straight(rosa)
    elif left_sensor < black_threshold and right_sensor > white_threshold: # Left sensor sees black, right sensor sees white -> turn left
        set_left(rosa)
    elif left_sensor > white_threshold and right_sensor < black_threshold: # Left sensor sees white, right sensor sees black -> turn right
        set_right(rosa)
    

if __name__ == '__main__':
    rosa = Rosa('rosa.local')

    while True:
        reflected = rosa.ground_reflected
        
        # follow_line_as_Thymio(rosa, reflected)
        
        left_sensor = reflected[0]
        right_sensor = reflected[1]

        right_wheel_speed = 0
        left_wheel_speed = 0

        difference = abs(left_sensor - right_sensor)

        if difference < THRESHOLD_DIFFERENCE:
            if following_left_edge:
                set_right(rosa)
            else:
                set_left(rosa)
        else:
            set_straight(rosa)
            following_left_edge = left_sensor > right_sensor
        time.sleep(0.16)
        