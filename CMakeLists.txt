PROJECT (OpenIMU)

SET(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)
SET(BUILD_SHARED_LIBS TRUE)

set(CMAKE_VERBOSE_MAKEFILE ON)

include(CTest)
include(CheckFunctionExists)

#Look for minimum cmake version
cmake_minimum_required(VERSION 3.0.2)
#set (CMAKE_CXX_STANDARD 14)

# compile in debug or release mode
IF(NOT CMAKE_BUILD_TYPE)
  #SET(CMAKE_BUILD_TYPE Release)
  SET(CMAKE_BUILD_TYPE Debug)
ENDIF(NOT CMAKE_BUILD_TYPE)

#First, let's compile our dependencies
#add_subdirectory(third_party)

#Then, compile our actimetry library
#add_subdirectory(lib_actimetry)

#Python
add_subdirectory(python)
