cmake_minimum_required(VERSION 3.16)
project(abm_io_model VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Eigen3 — header-only
find_package(Eigen3 3.4 REQUIRED NO_MODULE)

# Модуль симуляции (Приложение Б)
add_executable(simulate simulate.cpp)
target_link_libraries(simulate PRIVATE Eigen3::Eigen)
target_compile_options(simulate PRIVATE -O2 -Wall)

# Модуль калибровки (Приложение А)
add_executable(calibrate calibrate.cpp)
target_link_libraries(calibrate PRIVATE Eigen3::Eigen)
target_compile_options(calibrate PRIVATE -O2 -Wall)

# Инструкции сборки:
#   mkdir build && cd build
#   cmake .. -DCMAKE_BUILD_TYPE=Release
#   cmake --build .
