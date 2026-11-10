cmake_minimum_required(VERSION 3.8)
project(asv_simulator)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(ros_gz_sim REQUIRED)
find_package(ros_gz_bridge REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)
find_package(gz-transport13 REQUIRED)
find_package(gz-sensors8 REQUIRED)

# PX4 GenericMotorModel system used by the BlueROV2 Heavy model.
# It is built here against the same Gazebo Harmonic libraries used by this
# simulator, avoiding binary incompatibilities with external containers.
add_library(GenericMotorModelPlugin SHARED
  plugins/generic_motor/GenericMotorModel.cpp
)

target_include_directories(GenericMotorModelPlugin PRIVATE
  plugins/generic_motor
)

target_link_libraries(GenericMotorModelPlugin
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
  gz-transport13::gz-transport13
  gz-sensors8::gz-sensors8
)

install(TARGETS GenericMotorModelPlugin
  LIBRARY DESTINATION lib
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

install(PROGRAMS
  scripts/virtual_sonar.py
  scripts/gazebo_odom.py
  scripts/gazebo_odom_x500.py
  scripts/odometry_tf_broadcaster.py
  scripts/global_frame_manager.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  models
  urdf
  configs
  map
  worlds
  include
  # scripts/virtual_sonar.py
  # scripts/gazebo_odom.py
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
