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
set(GZ_SIM_VER ${gz-sim8_VERSION_MAJOR})

find_package(gz-common5 REQUIRED COMPONENTS graphics)
set(GZ_COMMON_VER ${gz-common5_VERSION_MAJOR})
find_package(gz-fuel_tools9 REQUIRED)
find_package(gz-math7 REQUIRED)
set(GZ_MATH_VER ${gz-math7_VERSION_MAJOR})
find_package(gz-msgs10 REQUIRED)
set(GZ_MSGS_VER ${gz-msgs10_VERSION_MAJOR})
find_package(gz-transport13 REQUIRED)
set(GZ_TRANSPORT_VER ${gz-transport13_VERSION_MAJOR})
find_package(gz-plugin2 REQUIRED COMPONENTS loader register)
set(GZ_PLUGIN_VER ${gz-plugin2_VERSION_MAJOR})
find_package(gz-rendering8 REQUIRED)
set(GZ_RENDERING_VER ${gz-rendering8_VERSION_MAJOR})
find_package(gz-sensors8 REQUIRED)
set(GZ_SENSORS_VER ${gz-sensors8_VERSION_MAJOR})
find_package(gz-utils2 REQUIRED)
set(GZ_UTILS_VER ${gz-utils2_VERSION_MAJOR})
find_package(sdformat14 REQUIRED)
find_package(Eigen3 REQUIRED)


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

add_library(Waves SHARED
  plugins/Wavefield.cc
)
set_target_properties(Waves PROPERTIES OUTPUT_NAME ASVWaves)
target_include_directories(Waves PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(Waves PUBLIC
  gz-common${GZ_COMMON_VER}::gz-common${GZ_COMMON_VER}
  gz-sim${GZ_SIM_VER}::core
  gz-math${GZ_MATH_VER}
  Eigen3::Eigen
)
install(
  TARGETS Waves
  DESTINATION lib)

add_library(Surface SHARED
  plugins/Surface.cc
)
set_target_properties(Surface PROPERTIES OUTPUT_NAME ASVSurface)
target_include_directories(Surface PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(Surface PUBLIC
  gz-sim${GZ_SIM_VER}::core
  gz-plugin${GZ_PLUGIN_VER}::gz-plugin${GZ_PLUGIN_VER}
  gz-rendering${GZ_RENDERING_VER}::gz-rendering${GZ_RENDERING_VER}
  gz-sensors${GZ_SENSORS_VER}::gz-sensors${GZ_SENSORS_VER}
  gz-utils${GZ_UTILS_VER}::gz-utils${GZ_UTILS_VER}
  Waves
  Eigen3::Eigen
)
install(
  TARGETS Surface
  DESTINATION lib)

add_library(WaveVisual SHARED
  plugins/WaveVisual.cc
)
set_target_properties(WaveVisual PROPERTIES OUTPUT_NAME ASVWaveVisual)
target_include_directories(WaveVisual PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_link_libraries(WaveVisual PUBLIC
  gz-sim${GZ_SIM_VER}::core
  gz-plugin${GZ_PLUGIN_VER}::gz-plugin${GZ_PLUGIN_VER}
  gz-transport${GZ_TRANSPORT_VER}::gz-transport${GZ_TRANSPORT_VER}
  gz-msgs${GZ_MSGS_VER}::gz-msgs${GZ_MSGS_VER}
  Waves
)
install(TARGETS WaveVisual
  DESTINATION lib)

add_library(PolyhedraBuoyancyDrag SHARED
  plugins/PolyhedraBuoyancyDrag.cc
  plugins/PolyhedronVolume.cc
  plugins/ShapeVolume.cc
)
set_target_properties(PolyhedraBuoyancyDrag PROPERTIES OUTPUT_NAME ASVPolyhedraBuoyancyDrag)
target_include_directories(PolyhedraBuoyancyDrag PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(PolyhedraBuoyancyDrag PUBLIC
  gz-sim${GZ_SIM_VER}::core
  gz-plugin${GZ_PLUGIN_VER}::gz-plugin${GZ_PLUGIN_VER}
  gz-transport${GZ_TRANSPORT_VER}::gz-transport${GZ_TRANSPORT_VER}
  gz-msgs${GZ_MSGS_VER}::gz-msgs${GZ_MSGS_VER}
  Waves
  Eigen3::Eigen
)
install(TARGETS PolyhedraBuoyancyDrag
  DESTINATION lib)

install(PROGRAMS
  scripts/virtual_sonar.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  models
  urdf
  configs
  worlds
  include
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
