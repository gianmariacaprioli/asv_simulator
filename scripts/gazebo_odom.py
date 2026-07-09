#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class GazeboOdom(Node):

    def __init__(self):
        super().__init__('gazebo_odom')

        self.tf_broadcaster = TransformBroadcaster(self)

        self.sub = self.create_subscription(
            Odometry,
            "/model/vessel_v2/odometry",
            self.callback,
            10)

    def callback(self, msg):
        tf = TransformStamped()

        # IL FIX È QUI: Usiamo l'esatto timestamp generato da Gazebo
        tf.header.stamp = msg.header.stamp
        tf.header.frame_id = "odom"
        tf.child_frame_id = "base_link"

        tf.transform.translation.x = msg.pose.pose.position.x
        tf.transform.translation.y = msg.pose.pose.position.y
        tf.transform.translation.z = msg.pose.pose.position.z

        tf.transform.rotation = msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(tf)
   
def main():
    rclpy.init()
    node = GazeboOdom()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()