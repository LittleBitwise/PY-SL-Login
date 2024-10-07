# Relative imports
from .packet import *
from .types import *

fixed = Fixed()
low = Low()
medium = Medium()
high = High()

string = String()
uuid = Uuid()
f32 = F32()
u32 = U32()
u16 = U16()
u8 = U8()
variable1 = Variable1()
variable2 = Variable2()
vector = Vector()
rotation = Rotation()
bool = Bool()

# Common constants
ZEROCODED = 0b1000_0000
RELIABLE = 0b0100_0000
RESENT = 0b0010_0000
ACKNOWLEDGE = 0b0001_0000

BODY_BYTE = 6

# Common message IDs
UseCircuitCode = low | 3
RegionHandshakeReply = low | 149
UUIDNameRequest = low | 235
CompleteAgentMovement = low | 249
CompletePingCheck = high | 2
AgentUpdate = high | 4
PacketAck = 0xFFFFFFFB
