cmake_minimum_required(VERSION 3.16)
project(abm_leontief CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Eigen3 3.4 REQUIRED NO_MODULE)

add_executable(simulate main.cpp)
target_link_libraries(simulate Eigen3::Eigen)
target_compile_options(simulate PRIVATE -O3 -march=native)
