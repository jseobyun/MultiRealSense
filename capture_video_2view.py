import pyrealsense2 as rs
import cv2
import os
import json
import numpy as np
import time
import argparse

from collections import defaultdict
from device_manager import DeviceManager

def parse_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_name', default='default')
    parser.add_argument('--no_save', action='store_true', default=False)
    args = parser.parse_args()
    return args

def capture(root):
    # Define some constants
    save_intrinsic = True
    L515_resolution_width = 1024  # pixels
    L515_resolution_height = 768  # pixels
    L515_frame_rate = 30

    resolution_width = 1280  # 1280 # pixels
    resolution_height = 720  # 720 # pixels
    frame_rate = 30  # fps

    dispose_frames_for_stablisation = 30  # frames
    try:
        # Enable the streams from all the intel realsense devices
        L515_rs_config = rs.config()
        L515_rs_config.enable_stream(rs.stream.depth, L515_resolution_width, L515_resolution_height, rs.format.z16,
                                     L515_frame_rate)
        L515_rs_config.enable_stream(rs.stream.infrared, 0, L515_resolution_width, L515_resolution_height, rs.format.y8,
                                     L515_frame_rate)
        L515_rs_config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, frame_rate)

        rs_config = rs.config()
        rs_config.enable_stream(rs.stream.depth, resolution_width, resolution_height, rs.format.z16, frame_rate)
        rs_config.enable_stream(rs.stream.infrared, 1, resolution_width, resolution_height, rs.format.y8, frame_rate)
        rs_config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, frame_rate)

        # Use the device manager class to enable the devices and get the frames
        device_manager = DeviceManager(rs.context(), rs_config, L515_rs_config)
        device_manager.enable_all_devices()
        print("Check the screen")
        start = time.time()
        for _ in range(300):
            frames = device_manager.get_frames(root, save=False, no_count=True)
            if save_intrinsic:
                intrinsic = device_manager.get_device_intrinsics(frames)
                with open(os.path.join(root, 'intrinsic.json'), 'w') as json_file:
                    json.dump(intrinsic, json_file)
                save_intrinsic = False
        end = time.time()
        print(end-start)
        print("Recording start")
        while True:
            frames = device_manager.get_frames(root, save=not args.no_save)


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
