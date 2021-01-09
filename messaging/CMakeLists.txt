

# Main cereal messaging library
add_library(cereal-messaging SHARED
    # "include/cereal/messaging/impl_msgq.hpp"
    # "include/cereal/messaging/impl_zmq.hpp"
    # "include/cereal/messaging/messaging.hpp"
    # "include/cereal/messaging/msgq.hpp"

    messaging.cc
    impl_zmq.cc
    impl_msgq.cc
    msgq.cc
    socketmaster.cc)
target_link_libraries(cereal-messaging cereal-objects cereal-services zmq)
target_include_directories(cereal-messaging PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Cereal messaging bridge
add_executable(cereal-messaging-bridge
    bridge.cc
)
target_link_libraries(cereal-messaging-bridge cereal-messaging libzmq)

# Cereal cython code
add_cython_target(messaging_pyx
    messaging_pyx.pyx CXX PY3
)

add_library(messaging_pyx MODULE ${messaging_pyx})
target_link_libraries(messaging_pyx Python::Python cereal-messaging)
set_target_properties(messaging_pyx PROPERTIES PREFIX "")
