cmake_minimum_required(VERSION 3.22.1)
project(soulgold_m6a2 LANGUAGES CXX)
add_library(soulgold_m6a2 SHARED native_bridge.cpp)
target_link_libraries(soulgold_m6a2 android log dl)
