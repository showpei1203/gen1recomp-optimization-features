cmake_minimum_required(VERSION 3.20)
project(SoulGoldRecomp C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(GBARECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../gbarecomp"
    CACHE PATH "Path to pinned gbarecomp checkout")
set(SOULGOLD_RECOMP_GENERATED_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/variants/soulgold/generated"
    CACHE PATH "Directory containing SoulGold gba_recompile output")

if(NOT EXISTS "${GBARECOMP_ROOT}/CMakeLists.txt")
    message(FATAL_ERROR "GBARECOMP_ROOT does not point to a gbarecomp checkout: ${GBARECOMP_ROOT}")
endif()
if(NOT EXISTS "${SOULGOLD_RECOMP_GENERATED_DIR}/dispatch_table.cpp")
    message(FATAL_ERROR
        "SoulGold generated corpus is missing. Run the R0 symbol import/recompile pipeline first: "
        "${SOULGOLD_RECOMP_GENERATED_DIR}")
endif()

# Asset packs use GBARecomp's data-only .gbamod catalog. Native hooks remain
# reviewed game-owned code linked into this executable.
set(GBARECOMP_ENABLE_MODS ON CACHE BOOL
    "Enable SoulGold data-only .gbamod catalog" FORCE)

add_subdirectory("${GBARECOMP_ROOT}" gbarecomp_build EXCLUDE_FROM_ALL)

file(GLOB SOULGOLD_GENERATED CONFIGURE_DEPENDS
    "${SOULGOLD_RECOMP_GENERATED_DIR}/recompiled_*.cpp")
list(APPEND SOULGOLD_GENERATED
    "${SOULGOLD_RECOMP_GENERATED_DIR}/dispatch_table.cpp")
foreach(optional_source symbol_map.cpp data_symbol_map.cpp)
    if(EXISTS "${SOULGOLD_RECOMP_GENERATED_DIR}/${optional_source}")
        list(APPEND SOULGOLD_GENERATED
            "${SOULGOLD_RECOMP_GENERATED_DIR}/${optional_source}")
    endif()
endforeach()

if(NOT SOULGOLD_GENERATED)
    message(FATAL_ERROR "No SoulGold recompiled shards found")
endif()

add_executable(SoulGoldRecomp
    src/main.cpp
    ${SOULGOLD_GENERATED})

# Generated guest code is large; use bounded optimization/debug cost like the
# public Pokemon recomp projects.
set(SOULGOLD_RECOMPILED_SOURCES ${SOULGOLD_GENERATED})
list(FILTER SOULGOLD_RECOMPILED_SOURCES INCLUDE REGEX
    "/recompiled_[0-9]+\\.cpp$")
if(SOULGOLD_RECOMPILED_SOURCES)
    set_source_files_properties(${SOULGOLD_RECOMPILED_SOURCES} PROPERTIES
        COMPILE_OPTIONS "-O1;-g0")
endif()

target_include_directories(SoulGoldRecomp PRIVATE
    "${GBARECOMP_ROOT}/src/armv4t"
    "${GBARECOMP_ROOT}/src/gba"
    "${GBARECOMP_ROOT}/src/runtime"
    "${GBARECOMP_ROOT}/src/debug"
    src)

if(APPLE OR MSVC)
    target_link_libraries(SoulGoldRecomp PRIVATE
        gbarecomp_runtime
        gbarecomp_debug
        gbarecomp_gba
        gbarecomp_armv4t)
else()
    target_link_libraries(SoulGoldRecomp PRIVATE
        -Wl,--start-group
        gbarecomp_runtime
        gbarecomp_debug
        gbarecomp_gba
        gbarecomp_armv4t
        -Wl,--end-group)
endif()

target_compile_definitions(SoulGoldRecomp PRIVATE
    GBARECOMP_DEFAULT_DEBUG_PORT=19905
    GBARECOMP_WINDOW_TITLE="SoulGoldRecomp"
    SOULGOLD_RECOMP_DEFAULT_GAME_CONFIG="variants/soulgold/game.toml")

# Keep enough host stack for a very large generated corpus on Windows.
if(MSVC)
    target_link_options(SoulGoldRecomp PRIVATE /STACK:268435456)
elseif(MINGW OR WIN32)
    target_link_options(SoulGoldRecomp PRIVATE -Wl,--stack,268435456)
endif()
