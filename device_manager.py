import pyrealsense2 as rs
import numpy as np
import cv2
import os

class Device:
    def __init__(self, pipeline, pipeline_profile, product_line):
        self.pipeline = pipeline
        self.pipeline_profile = pipeline_profile
        self.product_line = product_line


def enumerate_connected_devices(context):
    connect_device = []

    for d in context.devices:
        if d.get_info(rs.camera_info.name).lower() != 'platform camera':
            serial = d.get_info(rs.camera_info.serial_number)
            product_line = d.get_info(rs.camera_info.product_line)
            device_info = (serial, product_line)  # (serial_number, product_line)
            connect_device.append(device_info)
    return connect_device


def post_process_depth_frame(depth_frame, decimation_magnitude=1.0, spatial_magnitude=2.0, spatial_smooth_alpha=0.5,
                             spatial_smooth_delta=20, temporal_smooth_alpha=0.4, temporal_smooth_delta=20):
    # Post processing possible only on the depth_frame
    assert (depth_frame.is_depth_frame())

    # Available filters and control options for the filters
    decimation_filter = rs.decimation_filter()
    spatial_filter = rs.spatial_filter()
    temporal_filter = rs.temporal_filter()

    filter_magnitude = rs.option.filter_magnitude
    filter_smooth_alpha = rs.option.filter_smooth_alpha
    filter_smooth_delta = rs.option.filter_smooth_delta

    # Apply the control parameters for the filter
    decimation_filter.set_option(filter_magnitude, decimation_magnitude)
    spatial_filter.set_option(filter_magnitude, spatial_magnitude)
    spatial_filter.set_option(filter_smooth_alpha, spatial_smooth_alpha)
    spatial_filter.set_option(filter_smooth_delta, spatial_smooth_delta)
    temporal_filter.set_option(filter_smooth_alpha, temporal_smooth_alpha)
    temporal_filter.set_option(filter_smooth_delta, temporal_smooth_delta)

    # Apply the filters
    filtered_frame = decimation_filter.process(depth_frame)
    filtered_frame = spatial_filter.process(filtered_frame)
    filtered_frame = temporal_filter.process(filtered_frame)

    return filtered_frame

class DeviceManager:
    def __init__(self, context, D400_pipeline_configuration, L500_pipeline_configuration=rs.config()):
        assert isinstance(context, type(rs.context()))
        assert isinstance(D400_pipeline_configuration, type(rs.config()))
        assert isinstance(L500_pipeline_configuration, type(rs.config()))
        self._context = context
        self._available_devices = enumerate_connected_devices(context)
        self._enabled_devices = {}  # serial numbers of te enabled devices
        self.D400_config = D400_pipeline_configuration
        self.L500_config = L500_pipeline_configuration
        self._frame_counter = 0

    def enable_device(self, device_info, enable_ir_emitter):
        pipeline = rs.pipeline()

        device_serial = device_info[0]
        product_line = device_info[1]

        if product_line == "L500":
            # Enable L515 device
            self.L500_config.enable_device(device_serial)
            pipeline_profile = pipeline.start(self.L500_config)
        else:
            # Enable D400 device
            self.D400_config.enable_device(device_serial)
            pipeline_profile = pipeline.start(self.D400_config)

        # Set the acquisition parameters
        sensor = pipeline_profile.get_device().first_depth_sensor()
        self.depth_scale= sensor.get_depth_scale()*1000
        print(self.depth_scale)
        preset = rs.l500_visual_preset.max_range
        sensor.set_option(rs.option.visual_preset, int(preset))
        if sensor.supports(rs.option.emitter_enabled):
            sensor.set_option(rs.option.emitter_enabled, 1 if enable_ir_emitter else 0)
        self._enabled_devices[device_serial] = (Device(pipeline, pipeline_profile, product_line))

    def enable_all_devices(self, enable_ir_emitter=False):
        print(str(len(self._available_devices)) + " devices have been found")
        for device_info in self._available_devices:
            self.enable_device(device_info, enable_ir_emitter)

    def enable_emitter(self, enable_ir_emitter=True):
        for (device_serial, device) in self._enabled_devices.items():
            # Get the active profile and enable the emitter for all the connected devices
            sensor = device.pipeline_profile.get_device().first_depth_sensor()
            if not sensor.supports(rs.option.emitter_enabled):
                continue
            sensor.set_option(rs.option.emitter_enabled, 1 if enable_ir_emitter else 0)
            if enable_ir_emitter:
                sensor.set_option(rs.option.laser_power, 330)

    def get_frames(self, root, save=False, no_count=False):
        align_to = rs.stream.color
        align = rs.align(align_to)
        frames = {}
        while len(frames) < len(self._enabled_devices.items()):
            for cam_idx, (serial, device) in enumerate(self._enabled_devices.items()):
                streams = device.pipeline_profile.get_streams()
                frameset = device.pipeline.poll_for_frames()

                if frameset.size() == len(streams):
                    dev_info = (serial, device.product_line)
                    frames[dev_info] = {}
                    for stream in streams:
                        if (rs.stream.infrared == stream.stream_type()):
                            frame = frameset.get_infrared_frame(stream.stream_index())
                            key_ = (stream.stream_type(), stream.stream_index())
                        else:
                            frame = frameset.first_or_default(stream.stream_type())
                            key_ = stream.stream_type()
                        frames[dev_info][key_] = frame

                    aligned_frames = align.process(frameset)
                    aligned_depth = aligned_frames.get_depth_frame()
                    aligned_color = aligned_frames.get_color_frame()
                    rgb = np.asarray(aligned_color.get_data())
                    depth = np.array(aligned_depth.get_data(), dtype=np.float32)*self.depth_scale
                    depth = np.array(depth, np.uint16)
                    cv2.imshow(serial, rgb)
                    cv2.waitKey(1)
                    if save:
                        cv2.imwrite(os.path.join(root, f'images/view{cam_idx}/{self._frame_counter}_img.png'), rgb)
                        cv2.imwrite(os.path.join(root, f'depths/view{cam_idx}/{self._frame_counter}_depth.png'), depth)
        if not no_count:

            self._frame_counter += 1

        return frames


    def get_device_intrinsics(self, frames):
        """
        Get the intrinsics of the imager using its frame delivered by the realsense device

        Parameters:
        -----------
        frames : rs::frame
                 The frame grabbed from the imager inside the Intel RealSense for which the intrinsic is needed

        Return:
        -----------
        device_intrinsics : dict
        keys  : serial
                Serial number of the device
        values: [key]
                Intrinsics of the corresponding device
        """
        device_intrinsics = {}
        for (dev_info, frameset) in frames.items():
            serial = dev_info[0]
            device_intrinsics[serial] = {}
            for key, value in frameset.items():
                device_intrinsics[serial][key] = value.get_profile().as_video_stream_profile().get_intrinsics()
        print(device_intrinsics)
        return device_intrinsics

    def get_depth_to_color_extrinsics(self, frames):
        """
        Get the extrinsics between the depth imager 1 and the color imager using its frame delivered by the realsense device

        Parameters:
        -----------
        frames : rs::frame
                 The frame grabbed from the imager inside the Intel RealSense for which the intrinsic is needed

        Return:
        -----------
        device_intrinsics : dict
        keys  : serial
                Serial number of the device
        values: [key]
                Extrinsics of the corresponding device
        """
        device_extrinsics = {}
        for (dev_info, frameset) in frames.items():
            serial = dev_info[0]
            device_extrinsics[serial] = frameset[
                rs.stream.depth].get_profile().as_video_stream_profile().get_extrinsics_to(
                frameset[rs.stream.color].get_profile())
        return device_extrinsics

    def disable_streams(self):
        self.D400_config.disable_all_streams()
        self.L500_config.disable_all_streams()