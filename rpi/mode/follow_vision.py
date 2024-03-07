import cv2 as cv
from rosa import Rosa
import time

base_speed = 0.1
turn_ratio = 0.9
THRESHOLD_DIFFERENCE = 50
following_left_edge = True

# ROMEO : My objective is to clean up the code a little bit and change all the things that for me could explain the malfunctions of the robot.
# I do not have a way to test my code, I'm just changing things solely based on what I observed in your code which means that there will probably problems with my changes too, so I'm counting on you to verify that my changes are beneficial. 
# I'll leave comments everywhere I change something with what I changed and why, to help you understand my changes.
# To find all my changes, you can ctrl+f "ROMEO"
# (I also deleted every commented debug lines to clean the code, except my explanations obviously)

# General question : Where exactly is the AI in this ? This code seems to only use image analysis algorithms, except if the open_cv method findContours uses AI ? 

def get_line_centers(img, near_band_center_y, band_height, band_width_ratio, vmax, render=False):
    height, width, _ = img.shape
    band_width = int(width * band_width_ratio)
    x1 = (width - band_width) // 2
    x2 = x1 + band_width

    # ROMEO : With the arbitrary values you chose, near_y2 ends up outside of the img array.
    # If this array is a NumPy array, it won't be a problem, but if it's not, it could prevent the whole near_center calculation.
    near_y1, near_y2 = (near_band_center_y - band_height // 2, near_band_center_y + band_height // 2)
    near_band = img[near_y1:near_y2, x1:x2]

    # far_y1, far_y2 = (far_band_center_y - band_height // 2, far_band_center_y + band_height // 2)
    # far_band = img[far_y1:far_y2, x1:x2]

    if render:
        cv.rectangle(img, (x1, near_y1), (x2, near_y2), (255, 0, 0), 2)  # Near band (blue rectangle)
        # cv.rectangle(img, (x1, far_y1), (x2, far_y2), (0, 255, 0), 2)    # Far band (green rectangle)

    def process_band(band, offset_y):
        _, _, v = cv.split(cv.cvtColor(band, cv.COLOR_BGR2HSV))
        
        # ROMEO : What's the point of this ? If every pixel whose value exceeds 75 is converted to 0, isn't there a risk that that would create huge black areas that could offset the contours calculations ? 
        v[v > vmax] = 0
        _, contours, _ = cv.findContours(v, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return None
        contours = sorted(contours, key=cv.contourArea, reverse=True)
        cnt = contours[0]
        m = cv.moments(cnt)
        if m['m00'] > 0:
            cx, cy = (int(m['m10'] / m['m00']), int(m['m01'] / m['m00']))
            cx, cy = cx + x1, cy + offset_y
            if render:
                cv.circle(img, (cx, cy), 10, (0, 0, 255), -1)
            return (cx, cy)
        return None

    near_center = process_band(near_band, near_y1)
    # far_center = process_band(far_band, far_y1)

    return near_center

def follow_line(rosa, near_center, base_speed=0.1, gain=0.1, img_width=640):
    # Calculate the deviation from the center
    
    # ROMEO : Why not use the same deviation formula as in treasure.py (heading = object.center[0] - 170 // speed = 0.25 if heading > 0 else -0.25) ? 
    # If there's no particular point, why not choose one and use it in both files for continuity sake ?
    near_dx = ((near_center[0] / img_width) - 0.5) * 2

    ls = base_speed + gain * near_dx
    rs = base_speed - gain * near_dx

    rosa.left_wheel.speed = ls
    rosa.right_wheel.speed = rs

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

def combined_follow_line(rosa, near_center, reflected):
    global following_left_edge
    if near_center is not None:
        # Utiliser le suivi de ligne par caméra
        follow_line(rosa, near_center)
    else:
        # Utiliser le suivi de ligne par capteur
        left_sensor, right_sensor = reflected
        difference = abs(left_sensor - right_sensor)

        if difference < THRESHOLD_DIFFERENCE:
            if following_left_edge:
                set_right(rosa)
            else:
                set_left(rosa)
        else:
            set_straight(rosa)
            following_left_edge = left_sensor > right_sensor

if __name__ == '__main__':
    rosa = Rosa('rosa.local', local_robot=False)
    while True:

        near_center  = None
        # Mise à jour des données de la caméra
        img = rosa.camera.last_frame
        if img is not None:
            height, width, _ = img.shape
            near_center = get_line_centers(img, near_band_center_y=height - 10, band_height=30, band_width_ratio=0.6, vmax=75, render=True)

        # Mise à jour des données des capteurs
        reflected = rosa.ground_reflected

        # Combinaison des méthodes de suivi de ligne
        combined_follow_line(rosa, near_center, reflected)

        time.sleep(0.16)