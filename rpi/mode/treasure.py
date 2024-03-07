import logging
from rosa import Rosa
from time import sleep
import math

# ROMEO : My objective is to clean up the code a little bit and change all the things that for me could explain the malfunctions of the robot.
# I do not have a way to test my code, I'm just changing things solely based on what I observed in your code which means that there will probably problems with my changes too, so I'm counting on you to verify that my changes are beneficial. 
# I'll leave comments everywhere I change something with what I changed and why, to help you understand my changes.
# To find all my changes, you can ctrl+f "ROMEO"
# (I also deleted every commented debug lines to clean the code, except my explanations obviously)

chosen = None
chosen_bonus = 0
_home_distance = 0.0
_scan_distance = 0.0
_scan_speed = 0.03
logger = logging.getLogger(__name__)

def set_led_color(rosa, color):
    """Set LED color based on the robot's current state."""
    if color == 'blue':
        rosa.leds.bottom.left.color = [0, 0, 32] 
        rosa.leds.bottom.right.color = [0, 0, 32]
    elif color == 'red':
        rosa.leds.bottom.left.color = [32, 0, 0] 
        rosa.leds.bottom.right.color = [32, 0, 0]
    elif color == 'green':
        rosa.leds.bottom.left.color = [0, 32, 0]
        rosa.leds.bottom.right.color = [0, 32, 0]

# ROMEO : Removed the argument 'rosa' which wasn't used.
def flush():
    """Reset chosen, flush image buffer."""
    global _home_distance
    global chosen
    global chosen_bonus
    logger.info(f"COLLECTOR flush buffers")
    chosen = None
    chosen_bonus = 0
    _home_distance = 0.0
    
    # ROMEO : Changed 'for i in range(3):
    #     # _ = rosa.camera.last_frame
    #     sleep(0.2)'
    # We don't need a loop just for that.
    sleep(0.6)

def set_speed(rosa, ls, rs):
    rosa.left_wheel.speed = ls
    rosa.right_wheel.speed = rs

# ROMEO : Changed : 'threshold=0.4'
# Later in the code, you were checking if the confidence of the object was higher than 0.7, so why not put this value as the threshold here and remove the check later ?
def choose_object(rosa, threshold=0.7):
    """
    Choose an object according to policy.
    Here, the object with the highest confidence.
    """
    found = None
        
    if rosa.camera.last_detection is None:
        set_led_color(rosa, 'red')
        rosa.sound.system(1)
        return []
    
    try:
        found = desirable(rosa.camera.last_detection)
    except ValueError:
        logger.warn("COLLECTOR ignore exception in Yolo3 rectangle drawing!")
    if not found:
        return []
    object = sorted(found, key=lambda v: v.confidence)[0]
    if object.confidence < threshold: # ROMEO : In the end, the good_candidate check happens here.
        return []
    logger.info(
        f"COLLECTOR choosing {object.label} at {object.center} score {object.confidence}"
    )
    return object

def desirable(objects):
    """Decide whether we want this kind of object."""
    return [x for x in objects if (x.label == "star" or x.label== "cube" or x.label == "ball")]

def scan(rosa):
    """Look around, turning slowly clockwise."""
    global _scan_distance
    global _scan_speed
    if abs(_scan_distance) > 100:
        _scan_speed = -_scan_speed
    set_speed(rosa, _scan_speed, -_scan_speed * 0.2)
    _scan_distance += _scan_speed / 0.03 * 2
    set_led_color(rosa, 'blue')

def stop(rosa):
    """Stop turning."""
    set_speed(rosa, 0, 0)

def track(rosa, object, multiplier=0.6):
    """
    Turn towards chosen object.
    Convert delta ±170 ~ ±45° ~ ± 900 ms at speed 0.25
    """
    
    # ROMEO : I don't really know how to change this part, but it's really confusing to me.
    # For example, let's say that the object.center[0] = 150. After the calculation, we end up with a duration of 0.06ms, which really doesn't seem to be enough.
    # Maybe we should add a verification of the position of the object.center, if it's sufficiently in the middle we can stop, else continue to rotate ?
    # This is a big change so I'm not gonna try, but it could be something to implement.
    
    heading = object.center[0] - 170 # ROMEO : I assume that 170 is half of the image's width ?
    speed = 0.25 if heading > 0 else -0.25
    duration = abs(heading / 170.0 * 0.900 * multiplier)
    logger.info(
        f"COLLECTOR tracking {object.label} object at heading {heading}"
    )
    set_speed(rosa, speed, -speed)
    sleep(duration)
    stop(rosa)

def is_close(object, multiplier=0.4, threshold=-10):
    """Do we think this object is close enough to grab?"""
    global _home_distance
    
    # ROMEO : Changed 'azimuth = (200 - object.center[0]) * multiplier
    # decision = azimuth < threshold or _home_distance > 2'
    # Firstly, we need to use the y coordinate, not the x.
    # Secondly, I don't understand what was the meaning of the 200 you used and the point of the multiplier. To verify that the object is close enough, I think we simply need to check if 
    # its y coordinate is high enough (= the center is low enough on the image) ?     
        
    decision = object.center > {"img.width"} - {"some threshold value"} # I don't know the size of the image nor what a good value for the threshold would be, but the idea is there.
    
    # ROMEO : Commented temporarily this log because it didn't make sense anymore.
    # logger.info(
    #     f"COLLECTOR is {object.label} at az {azimuth} ({_home_distance} from home) close? {'Yes' if decision else 'No'}"
    # )
    return decision

def grab(rosa, object, backup=2.0):
    """Grab the object and bring it back home."""
    logger.info(
        f"COLLECTOR grab {object.label} then back up additional {backup}"
    )
    
    # ROMEO : To be honest, I don't know how accurate this sequence is but I'll trust you.
    set_led_color(rosa, 'green')
    set_speed(rosa, 0.2, 0.2)
    sleep(2.4)
    set_speed(rosa,-0.25, 0.25)
    sleep(3.6)
    set_speed(rosa,0.20, 0.20)
    sleep(2.0 + backup)
    set_speed(rosa,-0.2, -0.2)
    sleep(1)
    set_speed(rosa,0.30, -0.30)
    sleep(3.0)
    set_speed(rosa, 0, 0)
    rosa.sound.system(4)
    set_led_color(rosa, 'blue')


def good_candidate():
    """Remember whether chosen_obj and chosen agree about the object."""
    # ROMEO : Changed 'global chosen
    # global chosen_bonus
    # if chosen:
    #     if chosen and chosen.label == chosen.label:
    #         chosen_bonus += 1
    #         logger.info(
    #             f"COLLECTOR good {chosen.label} bonus {chosen_bonus}"
    #         )
    #     return True
    # if chosen:
    #     logger.info(f"COLLECTOR lost {chosen.label}")
    # chosen = None
    # chosen_bonus = 0
    # return False'
    # The whole function was just checking if the object existed and incrementing chosen_bonus, whose value is never relevent anywhere (see explanation on line )
    # I also don't understand your documentation, at this point in your code chosen_obj (which I deleted because it wasn't used) and chosen are the same things so they will always agree.
    return

if __name__ == '__main__':
    rosa = Rosa('rosa.local')
    
    while True:

        chosen = choose_object(rosa)
        print(chosen) # ROMEO : Is this line important ?
        
        # ROMEO : Changed 'if not good_candidate() or chosen_bonus < 0'
        # With the changes I made to choose_object, if the object is not a good candidate (= choose_object returning []), we scan and flush, which is the same as before.  
        if not chosen:
            # Scan clockwise
            scan(rosa)
            flush(rosa)
            continue
        
        
        # ROMEO : Changed 'if chosen.confidence > 0.7 or chosen_bonus > 2'
        # We now check for the confidence in choose_object and chosen couldn't realistically get over 2, so this check was not relevent anymore.
        # Now, if choose_object returns something, we already know that it's a good candidate so we can continue.
        else:
            print(f"COLLECTOR high confidence for {chosen.label}")

            track(rosa, chosen)
            
            # ROMEO : Shouldn't all this happen after we're sure that the robot is done tracking the object and that it's correctly in front of the robot ? (See my comments inside the track function)
            if is_close(chosen):
                grab(rosa, chosen, backup=_home_distance)
                flush(rosa)
            else:
                set_speed(rosa, 0.1, 0.1)
                # Polling interval imposes backup ~ 1200 ms @
                _home_distance += 0.3
        
        # ROMEO : Removed 'else:
        # # Try to stabilize choice
        # set_speed(rosa, 0.06, 0.06)
        # chosen_bonus -= 1
        # logger.info(
        #     f"COLLECTOR try to focus on {chosen.label}, "
        #     f"bonus now {chosen_bonus}"
        # )'
        # I don't really see the point of trying to stabilize only once (because we were checking if chosen_bonus was inferior to 0, this stabilization could happen only once before it was considered a bad_candidate)
        # by going just a bit forward.
        
        

        sleep(0.016)