from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# must be build with scons
from .messaging_pyx import Context, Poller, SubSocket, PubSocket  # pylint: disable=no-name-in-module, import-error
from .messaging_pyx import MultiplePublishersError, MessagingError  # pylint: disable=no-name-in-module, import-error
import capnp

from typing import Optional, List, Union

from cereal import log
from cereal.services import service_list

assert MultiplePublishersError
assert MessagingError

# sec_since_boot is faster, but allow to run standalone too
try:
  from common.realtime import sec_since_boot
except ImportError:
  import time
  sec_since_boot = time.time
  print("Warning, using python time.time() instead of faster sec_since_boot")

context = Context()

def new_message(service: Optional[str] = None, size: Optional[int] = None) -> capnp.lib.capnp._DynamicStructBuilder:
  dat = log.Event.new_message()
  dat.logMonoTime = int(sec_since_boot() * 1e9)
  dat.valid = True
  if service is not None:
    if size is None:
      dat.init(service)
    else:
      dat.init(service, size)
  return dat

def pub_sock(endpoint: str) -> PubSocket:
  sock = PubSocket()
  sock.connect(context, endpoint)
  return sock

def sub_sock(endpoint: str, poller: Optional[Poller] = None, addr: str = "127.0.0.1",
             conflate: bool = False, timeout: Optional[int] = None) -> SubSocket:
  sock = SubSocket()
  sock.connect(context, endpoint, addr.encode('utf8'), conflate)

  if timeout is not None:
    sock.setTimeout(timeout)

  if poller is not None:
    poller.registerSocket(sock)
  return sock


def drain_sock_raw(sock: SubSocket, wait_for_one: bool = False) -> List[bytes]:
  """Receive all message currently available on the queue"""
  ret: List[bytes] = []
  while 1:
    if wait_for_one and len(ret) == 0:
      dat = sock.receive()
    else:
      dat = sock.receive(non_blocking=True)

    if dat is None:
      break

    ret.append(dat)

  return ret

def drain_sock(sock: SubSocket, wait_for_one: bool = False) -> List[capnp.lib.capnp._DynamicStructReader]:
  """Receive all message currently available on the queue"""
  ret: List[capnp.lib.capnp._DynamicStructReader] = []
  while 1:
    if wait_for_one and len(ret) == 0:
      dat = sock.receive()
    else:
      dat = sock.receive(non_blocking=True)

    if dat is None:  # Timeout hit
      break

    dat = log.Event.from_bytes(dat)
    ret.append(dat)

  return ret


# TODO: print when we drop packets?
def recv_sock(sock: SubSocket, wait: bool = False) -> Union[None, capnp.lib.capnp._DynamicStructReader]:
  """Same as drain sock, but only returns latest message. Consider using conflate instead."""
  dat = None

  while 1:
    if wait and dat is None:
      rcv = sock.receive()
    else:
      rcv = sock.receive(non_blocking=True)

    if rcv is None:  # Timeout hit
      break

    dat = rcv

  if dat is not None:
    dat = log.Event.from_bytes(dat)

  return dat

def recv_one(sock: SubSocket) -> Union[None, capnp.lib.capnp._DynamicStructReader]:
  dat = sock.receive()
  if dat is not None:
    dat = log.Event.from_bytes(dat)
  return dat

def recv_one_or_none(sock: SubSocket) -> Union[None, capnp.lib.capnp._DynamicStructReader]:
  dat = sock.receive(non_blocking=True)
  if dat is not None:
    dat = log.Event.from_bytes(dat)
  return dat

def recv_one_retry(sock: SubSocket) -> capnp.lib.capnp._DynamicStructReader:
  """Keep receiving until we get a message"""
  while True:
    dat = sock.receive()
    if dat is not None:
      return log.Event.from_bytes(dat)

class SubMaster():
  def __init__(self, services: List[str], poll: Optional[List[str]] = None,
               ignore_alive: Optional[List[str]] = None, addr:str ="127.0.0.1"):
    self.frame = -1
    self.updated = {s: False for s in services}
    self.rcv_time = {s: 0. for s in services}
    self.rcv_frame = {s: 0 for s in services}
    self.alive = {s: False for s in services}
    self.sock = {}
    self.freq = {}
    self.data = {}
    self.valid = {}
    self.logMonoTime = {}

    self.poller = Poller()
    self.non_polled_services = [s for s in services if poll is not None and
                                len(poll) and s not in poll]

    if ignore_alive is not None:
      self.ignore_alive = ignore_alive
    else:
      self.ignore_alive = []

    for s in services:
      if addr is not None:
        p = self.poller if s not in self.non_polled_services else None
        self.sock[s] = sub_sock(s, poller=p, addr=addr, conflate=True)
      self.freq[s] = service_list[s].frequency

      try:
        data = new_message(s)
      except capnp.lib.capnp.KjException:  # pylint: disable=c-extension-no-member
        data = new_message(s, 0) # lists

      self.data[s] = getattr(data, s)
      self.logMonoTime[s] = 0
      self.valid[s] = data.valid

  def __getitem__(self, s: str) -> capnp.lib.capnp._DynamicStructReader:
    return self.data[s]

  def update(self, timeout: int = 1000) -> None:
    msgs = []
    for sock in self.poller.poll(timeout):
      msgs.append(recv_one_or_none(sock))

    # non-blocking receive for non-polled sockets
    for s in self.non_polled_services:
      msgs.append(recv_one_or_none(self.sock[s]))
    self.update_msgs(sec_since_boot(), msgs)

  def update_msgs(self, cur_time: float, msgs: List[capnp.lib.capnp._DynamicStructReader]) -> None:
    self.frame += 1
    self.updated = dict.fromkeys(self.updated, False)
    for msg in msgs:
      if msg is None:
        continue

      s = msg.which()
      self.updated[s] = True
      self.rcv_time[s] = cur_time
      self.rcv_frame[s] = self.frame
      self.data[s] = getattr(msg, s)
      self.logMonoTime[s] = msg.logMonoTime
      self.valid[s] = msg.valid

    for s in self.data:
      # arbitrary small number to avoid float comparison. If freq is 0, we can skip the check
      if self.freq[s] > 1e-5:
        # alive if delay is within 5x the expected frequency
        self.alive[s] = (cur_time - self.rcv_time[s]) < (5. / self.freq[s])
      else:
        self.alive[s] = True

  def all_alive(self, service_list=None) -> bool:
    if service_list is None:  # check all
      service_list = self.alive.keys()
    return all(self.alive[s] for s in service_list if s not in self.ignore_alive)

  def all_valid(self, service_list=None) -> bool:
    if service_list is None:  # check all
      service_list = self.valid.keys()
    return all(self.valid[s] for s in service_list)

  def all_alive_and_valid(self, service_list=None) -> bool:
    if service_list is None:  # check all
      service_list = self.alive.keys()
    return self.all_alive(service_list=service_list) and self.all_valid(service_list=service_list)

class PubMaster():
  def __init__(self, services: List[str]):
    self.sock = {}
    for s in services:
      self.sock[s] = pub_sock(s)

  def send(self, s: str, dat: Union[bytes, capnp.lib.capnp._DynamicStructBuilder]) -> None:
    if not isinstance(dat, bytes):
      dat = dat.to_bytes()
    self.sock[s].send(dat)
