#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


class GlobalFrameManager(Node):

    def __init__(self):
        super().__init__('global_frame_manager')

        self.declare_parameter(
            'global_frame',
            'ocean_world'
        )

        self.declare_parameter(
            'odom_frames',
            ['odom']
        )

        self.global_frame = (
            self.get_parameter('global_frame')
            .get_parameter_value()
            .string_value
        )

        self.odom_frames = (
            self.get_parameter('odom_frames')
            .get_parameter_value()
            .string_array_value
        )

        self.static_broadcaster = StaticTransformBroadcaster(self)

        self.publish_global_transforms()

    def publish_global_transforms(self):

        transforms = []

        for odom_frame in self.odom_frames:

            tf_msg = TransformStamped()

            # Static TFs are valid for all times.
            tf_msg.header.stamp = self.get_clock().now().to_msg()

            tf_msg.header.frame_id = self.global_frame
            tf_msg.child_frame_id = odom_frame

            # Gazebo OdometryPublisher currently provides poses in a
            # world-aligned odometry frame, therefore world -> odom
            # is the identity transform.
            tf_msg.transform.translation.x = 0.0
            tf_msg.transform.translation.y = 0.0
            tf_msg.transform.translation.z = 0.0

            tf_msg.transform.rotation.x = 0.0
            tf_msg.transform.rotation.y = 0.0
            tf_msg.transform.rotation.z = 0.0
            tf_msg.transform.rotation.w = 1.0

            transforms.append(tf_msg)

        self.static_broadcaster.sendTransform(transforms)

        self.get_logger().info(
            f'Global frame: {self.global_frame}'
        )

        for odom_frame in self.odom_frames:
            self.get_logger().info(
                f'Publishing static TF: '
                f'{self.global_frame} -> {odom_frame}'
            )


def main(args=None):

    rclpy.init(args=args)

    node = GlobalFrameManager()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()