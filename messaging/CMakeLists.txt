

# Main cereal messaging library
add_library(cereal-messaging
    "include/cereal/messaging/impl_msgq.hpp"
    "include/cereal/messaging/impl_zmq.hpp"
    "include/cereal/messaging/messaging.hpp"
    "include/cereal/messaging/msgq.hpp"

    messaging.cc
    impl_zmq.cc
    impl_msgq.cc
    msgq.cc
    socketmaster.cc)
target_link_libraries(cereal-messaging cereal-objects cereal-services)
target_include_directories(cereal-messaging PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Cereal messaging bridge
add_executable(cereal-messaging-bridge
    bridge.cc
)
target_link_libraries(cereal-messaging-bridge cereal-messaging libzmq)

# Cereal cython code
add_cython_target(cereal-messaging-pyx
    messaging_pyx.pyx CXX PY3
)
add_library(cereal-messaging-pyx MODULE ${cereal-messaging-pyx})
target_link_libraries(cereal-messaging-pyx Python::Python cereal-messaging)
