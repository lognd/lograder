cmake_minimum_required(VERSION 3.15)

project(HelloWorld LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(HelloWorld hello_world.cpp)