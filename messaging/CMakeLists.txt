

# Main cereal messaging library
add_library(cereal-messaging
    ../services.h # implicit dependency on above
    messaging.cc
    messaging.hpp
    impl_zmq.cc
    impl_msgq.cc
    msgq.cc
    socketmaster.cc)
target_link_libraries(cereal-messaging cereal-objects)
target_include_directories(cereal-messaging PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Cereal messaging bridge
find_package(ZeroMQ REQUIRED)
add_executable(cereal-messaging-bridge
    ../services.h # implicit dependency on above
    bridge.cc
)
target_link_libraries(cereal-messaging-bridge cereal-messaging libzmq)

# Cereal cython code
find_package (Python COMPONENTS Interpreter Development REQUIRED) 
find_package(Cython REQUIRED)
# envCython.Program('messaging/messaging_pyx.so', 'messaging/messaging_pyx.pyx', LIBS=envCython["LIBS"]+[messaging_lib, "zmq"])
add_cython_target(cereal-messaging-pyx
    messaging_pyx.pyx CXX PY3
)
add_library(cereal-messaging-pyx MODULE ${cereal-messaging-pyx})
target_link_libraries(cereal-messaging-pyx Python::Python cereal-messaging)
