import pyrealsense2 as rs
import cv2
import os
import argparse
import numpy as np
import time

from collections import defaultdict
from device_manager import DeviceManager
def parse_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_name', default='default')
    parser.add_argument('--interval', default='4', type=int)
    args = parser.parse_args()
    return args

def capture(root):

    # Define some constants
    L515_resolution_width = 1024  # pixels
    L515_resolution_height = 768  # pixels
    L515_frame_rate = 30

    rgb_width = 1920
    rgb_height = 1080
    dispose_frames_for_stablisation = 30  # frames
    try:
        # Enable the streams from all the intel realsense devices
        first_rs_config = rs.config()
        first_rs_config.enable_stream(rs.stream.depth, L515_resolution_width, L515_resolution_height, rs.format.z16, L515_frame_rate)
        first_rs_config.enable_stream(rs.stream.infrared, L515_resolution_width, L515_resolution_height, rs.format.y8, L515_frame_rate)
        first_rs_config.enable_stream(rs.stream.color, rgb_width, rgb_height, rs.format.bgr8, L515_frame_rate)

        second_rs_config = rs.config()
        second_rs_config.enable_stream(rs.stream.depth, L515_resolution_width, L515_resolution_height, rs.format.z16, L515_frame_rate)
        second_rs_config.enable_stream(rs.stream.infrared, L515_resolution_width, L515_resolution_height, rs.format.y8, L515_frame_rate)
        second_rs_config.enable_stream(rs.stream.color, rgb_width, rgb_height, rs.format.bgr8, L515_frame_rate)

        # Use the device manager class to enable the devices and get the frames
        device_manager = DeviceManager(rs.context(), first_rs_config, second_rs_config)
        device_manager.enable_all_devices()
        print("Start")
        while True:
            frames = device_manager.get_frames(root, save=True)
            time.sleep(args.interval)
            print("Saved")


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
