#pragma once
#include <vector>
#include <string>
#include <unistd.h>

#include "cereal/messaging/messaging.hpp"
#include "cereal/visionipc/visionipc.h"
#include "cereal/visionipc/visionbuf.h"

class VisionIpcClient {
private:
  std::string name;
  Context * msg_ctx;
  SubSocket * sock;
  Poller * poller;

  VisionStreamType type;

  cl_device_id device_id = nullptr;
  cl_context ctx = nullptr;

  void init_msgq(bool conflate);

public:
  bool connected = false;
  int num_buffers = 0;
  VisionBuf buffers[VISIONIPC_MAX_FDS];
  VisionIpcClient(std::string name, VisionStreamType type, bool conflate, cl_device_id device_id=nullptr, cl_context ctx=nullptr);
  ~VisionIpcClient();
  VisionBuf * recv(VisionIpcBufExtra * extra=nullptr);
  bool connect(bool blocking=true);
};
