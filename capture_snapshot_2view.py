import pyrealsense2 as rs
import cv2
import os
from pynput.keyboard import Listener
import argparse
import numpy as np
import time

from collections import defaultdict
from device_manager import DeviceManager
def parse_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_name', default='test ')
    args = parser.parse_args()
    return args

def capture(root):

    # Define some constants
    L515_resolution_width = 1024  # pixels
    L515_resolution_height = 768  # pixels
    L515_frame_rate = 30

    resolution_width = 1024  # 1280 # pixels
    resolution_height = 768  # 720 # pixels
    frame_rate = 30  # fps

    rgb_width = 1920
    rgb_height = 1080
    dispose_frames_for_stablisation = 30  # frames
    try:
        # Enable the streams from all the intel realsense devices
        L515_rs_config = rs.config()
        L515_rs_config.enable_stream(rs.stream.depth, L515_resolution_width, L515_resolution_height, rs.format.z16, L515_frame_rate)
        L515_rs_config.enable_stream(rs.stream.infrared, L515_resolution_width, L515_resolution_height, rs.format.y8, L515_frame_rate)
        L515_rs_config.enable_stream(rs.stream.color, rgb_width, rgb_height, rs.format.bgr8, frame_rate)

        rs_config = rs.config()
        rs_config.enable_stream(rs.stream.depth, resolution_width, resolution_height, rs.format.z16, frame_rate)
        rs_config.enable_stream(rs.stream.infrared,  resolution_width, resolution_height, rs.format.y8, frame_rate)
        rs_config.enable_stream(rs.stream.color, rgb_width, rgb_height, rs.format.bgr8, frame_rate)

        # Use the device manager class to enable the devices and get the frames
        device_manager = DeviceManager(rs.context(), rs_config, L515_rs_config)
        device_manager.enable_all_devices()
        def on_press(key):
            if str(key) == "Key.space":
                frames = device_manager.get_frames(root, save=True)
                print("Current frame is caputred")
            else:
                frames = device_manager.get_frames(root, save=False)

        print("Waiting") 
        with Listener(on_press = on_press) as listener:
            listener.join()

    except KeyboardInterrupt:
        print("The program was interupted by the user. Closing the program...")

    finally:
        device_manager.disable_streams()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    args = parse_config()
    exp_name = args.exp_name
    root = f'./{exp_name}'
    if not os.path.exists(root):
        os.mkdir(root)
        os.mkdir(os.path.join(root, 'images'))
        os.mkdir(os.path.join(root, 'images', 'view0'))
        os.mkdir(os.path.join(root, 'images', 'view1'))
        os.mkdir(os.path.join(root, 'depths'))
        os.mkdir(os.path.join(root, 'depths', 'view0'))
        os.mkdir(os.path.join(root, 'depths', 'view1'))
    capture(root)
