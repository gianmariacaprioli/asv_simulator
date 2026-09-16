#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class X500OdometryTF(Node):

    def __init__(self):
        super().__init__('x500_odometry_tf')

        self.tf_broadcaster = TransformBroadcaster(self)

        self.subscription = self.create_subscription(
            Odometry,
            '/model/x500/odometry',
            self.odom_callback,
            10
        )

        self.get_logger().info(
            'Publishing TF: x500/odom -> x500/base_link'
        )

    def odom_callback(self, msg):

        tf_msg = TransformStamped()

        tf_msg.header.stamp = msg.header.stamp
        tf_msg.header.frame_id = 'x500/odom'
        tf_msg.child_frame_id = 'x500/base_link'

        tf_msg.transform.translation.x = msg.pose.pose.position.x
        tf_msg.transform.translation.y = msg.pose.pose.position.y
        tf_msg.transform.translation.z = msg.pose.pose.position.z

        tf_msg.transform.rotation = msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(tf_msg)


def main(args=None):

    rclpy.init(args=args)

    node = X500OdometryTF()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()