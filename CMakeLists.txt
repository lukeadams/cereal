project(Cereal)
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/cmake/")
    
# Build CapnProto prototypes
find_package(CapnProto)
capnp_generate_cpp(CAPNP_SRCS CAPNP_HDRS car.capnp log.capnp)
add_library(cereal-objects ${CAPNP_SRCS} ${CAPNP_HDRS})
target_link_libraries(cereal-objects PRIVATE CapnProto::capnp)
target_include_directories(cereal-objects PUBLIC ${PROJECT_BINARY_DIR})

# Generate service header
add_custom_command(OUTPUT services.h
    DEPENDS services.py service_list.yaml
    COMMAND python3 "${CMAKE_CURRENT_SOURCE_DIR}/services.py" > "services.h"
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
)
add_custom_target(cereal-services-file DEPENDS services.h) # target which depends on the command output above
add_library(cereal-services INTERFACE) # header only library
add_dependencies(cereal-services cereal-services-file) # Depend on the file target
target_include_directories(cereal-services INTERFACE ${CMAKE_CURRENT_BINARY_DIR})

add_subdirectory(messaging)
