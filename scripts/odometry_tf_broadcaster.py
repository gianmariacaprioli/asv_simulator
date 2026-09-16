#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class OdometryTFBroadcaster(Node):

    def __init__(self):
        super().__init__('odometry_tf_broadcaster')

        self.declare_parameter('odom_topic', '/odom')
        self.odom_topic = (
            self.get_parameter('odom_topic')
            .get_parameter_value()
            .string_value
        )

        self.tf_broadcaster = TransformBroadcaster(self)

        self.subscription = self.create_subscription(
            Odometry,
            self.odom_topic,
            self.odom_callback,
            10
        )

        self.warned_missing_frames = False

        self.get_logger().info(
            f'Broadcasting TF from Odometry topic: {self.odom_topic}'
        )

    def odom_callback(self, msg: Odometry):

        # The Odometry message itself defines the TF relationship:
        #
        #   msg.header.frame_id -> msg.child_frame_id
        #
        # Do not hard-code frame names here. This makes the node reusable
        # for any UAV / USV.
        if not msg.header.frame_id or not msg.child_frame_id:

            if not self.warned_missing_frames:
                self.get_logger().error(
                    f'Odometry message on {self.odom_topic} has empty '
                    'frame_id or child_frame_id.'
                )
                self.warned_missing_frames = True

            return

        tf_msg = TransformStamped()

        tf_msg.header.stamp = msg.header.stamp
        tf_msg.header.frame_id = msg.header.frame_id
        tf_msg.child_frame_id = msg.child_frame_id

        tf_msg.transform.translation.x = msg.pose.pose.position.x
        tf_msg.transform.translation.y = msg.pose.pose.position.y
        tf_msg.transform.translation.z = msg.pose.pose.position.z

        tf_msg.transform.rotation = msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(tf_msg)


def main(args=None):

    rclpy.init(args=args)

    node = OdometryTFBroadcaster()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()