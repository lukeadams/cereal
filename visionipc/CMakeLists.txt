
add_library(visionipc SHARED
    ipc.cc
    visionipc_server.cc
    visionipc_client.cc
    visionbuf.cc

    visionbuf_cl.cc
)


target_include_directories(visionipc PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(visionipc cereal-messaging)
