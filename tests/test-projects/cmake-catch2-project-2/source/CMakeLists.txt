cmake_minimum_required(VERSION 3.14)
project(MyCatch2Tests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.6.0
)

FetchContent_MakeAvailable(catch2)

add_executable(tests
    main.cpp
    test.cpp
)

target_link_libraries(tests
    PRIVATE Catch2::Catch2WithMain
)

include(CTest)
include(Catch)

catch_discover_tests(tests)