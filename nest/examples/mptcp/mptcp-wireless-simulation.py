# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2023 NITK Surathkal

########################
# SHOULD BE RUN AS ROOT
########################
from nest.topology import *
from nest.experiment import *
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper
from nest.input_validator.metric import Percentage

from nest import config

"""
# This config option is useful when experimenting with NeST.
# When set to True, NeST will match the topology against a checklist.
# This checklist defines the necessary checks that must pass if an MPTCP
# behaviour is to be expected from the topology.

# Note that passing all checks is not a confirmation that MPTCP behaviour
# will be seen in the experiment for sure.
"""
config.set_value("show_mptcp_checklist", True)

"""
# This program demonstrates MPTCP behavior in a wireless-like environment
# by simulating periodic packet loss on one of the paths using netem.
#
# The topology connects two hosts `h1` and `h2` via two routers R1, R2.
# H2 is multi-homed and multi-addressed.
# 
# Path 1 (via eth2a): Reliable wired connection with low latency
# Path 2 (via eth2b): Simulated wireless connection with periodic loss using 
#                     Gilbert-Elliot model to create burst errors typical
#                     of wireless fading
#
# This will demonstrate how MPTCP adapts to varying path conditions and
# provides resilience against wireless-like packet loss patterns.

################################################################################
#                                                                              #
#                            Network Topology                                  #
#                                                                              #
#      ____                 ____                 ____                ____      #
#     |    |               |    |               |    |  Good Path   |    |     #
#     |    |  100mbit,5ms  |    |  100mbit,5ms  |    | ------------ |    |     #
#     | H1 | ------------- | R1 | ------------- | R2 |   10mbit,5ms | H2 |     #
#     |    |               |    |               |    | ------------ |    |     #
#     |____|               |____|               |____|  Lossy Path  |____|     #
#                                                       (Wireless-              #
#                                                        like with              #
#                                                        burst loss)            #
#                                                                              #
################################################################################
"""

# In the topology, we have 4 different subnets:
# * One between H1-R1 (wired backbone)
# * One between R1-R2 (wired backbone) 
# * Two between R2-H2 (one reliable, one wireless-like with loss)
network1 = Network("10.0.0.0/24")     # H1-R1 backbone
network2 = Network("12.0.0.0/24")     # R1-R2 backbone  
network3 = Network("192.168.10.0/24") # R2-H2 reliable path
network4 = Network("192.168.11.0/24") # R2-H2 wireless-like path with loss

# Create two MPTCP enabled hosts `h1` and `h2`, and the routers 'r1' and 'r2'.
h1 = Node("h1")
h2 = Node("h2") 
r1 = Router("r1")
r2 = Router("r2")

# Enable MPTCP explicitly (though it's enabled by default)
h1.enable_mptcp()
h2.enable_mptcp()

"""
# add_mptcp_monitor() will run the MPTCP monitor on the specified node,
# during the experiment. The monitor shows the MPTCP connections and subflows
# created during the experiment with their flow information.

# The output is stored as a part of the experiment dump itself.
"""
h1.add_mptcp_monitor()
h2.add_mptcp_monitor()

# Connect `h1` to `h2` via `r1` and `r2` as per topology
(eth1a, etr1a) = connect(h1, r1, network=network1)
(etr1b, etr2a) = connect(r1, r2, network=network2)
(etr2b, eth2a) = connect(r2, h2, network=network3)  # Reliable path
(etr2c, eth2b) = connect(r2, h2, network=network4)  # Wireless-like path

# Assign IPv4 addresses to all the interfaces in the network.
AddressHelper.assign_addresses()

# Set up routing - both paths available for MPTCP
h1.add_route("DEFAULT", eth1a)
r1.add_route(eth2a.get_address(), etr1b)
r1.add_route(eth2b.get_address(), etr1b)  
r2.add_route(eth1a.get_address(), etr2a)
h2.add_route(eth1a.get_address(), eth2a)
h2.add_route(eth1a.get_address(), eth2b)

# Shape links according to the topology
# Backbone links - high capacity, low latency
eth1a.set_attributes("100mbit", "5ms") 
etr1a.set_attributes("100mbit", "5ms")
etr1b.set_attributes("100mbit", "5ms")
etr2a.set_attributes("100mbit", "5ms")

# Path 1: Reliable wired connection - moderate capacity, low latency
etr2b.set_attributes("10mbit", "5ms")
eth2a.set_attributes("10mbit", "5ms")

# Path 2: Wireless-like connection - lower capacity, higher latency, WITH LOSS
etr2c.set_attributes("8mbit", "25ms")  # Typical wireless latency
eth2b.set_attributes("8mbit", "25ms")

print("Setting up wireless-like packet loss on Path 2...")

# Apply Gilbert-Elliot model for wireless-like burst errors
# Parameters simulate wireless channel fading:
# - p=5%: Probability to enter bad state (wireless interference)
# - r=20%: Probability to recover from bad state (interference clears)
# - h=70%: Packet loss probability in bad state (severe fading)
# - k=0.1%: Background packet loss in good state (thermal noise)
etr2c.set_packet_loss_gemodel(
    p=Percentage("5%"),    # 5% chance to enter bad state
    r=Percentage("20%"),   # 20% chance to recover from bad state
    h=Percentage("30%"),   # 30% transmission success in bad state (70% loss)
    k=Percentage("0.1%")   # 0.1% loss in good state
)

# Also apply loss to the other end of the wireless-like link
eth2b.set_packet_loss_gemodel(
    p=Percentage("3%"),    # Slightly different parameters for asymmetry
    r=Percentage("25%"),   
    h=Percentage("25%"),   # 75% loss in bad state
    k=Percentage("0.05%")
)

print("Wireless simulation: Path 2 configured with Gilbert-Elliot loss model")
print("- Good state: 0.1% loss (background noise)")
print("- Bad state: 70-75% loss (severe fading)")
print("- State transition: 5% chance to bad, 20-25% chance to recover")

# Configure MPTCP parameters and flow for the topology.

## 1. Create a flow from eth1a to eth2a (primary destination)
flow = Flow(
    h1,
    h2, 
    eth2a.get_address(),
    0,      # start_time
    120,    # stop_time - longer to observe wireless effects
    1,      # number_of_streams
    source_address=eth1a.get_address(),
)

## 2. Allow H1 and H2 to create multiple subflows for multipath operation
h1.set_mptcp_parameters(max_subflows=2, max_add_addr_accepted=2)
h2.set_mptcp_parameters(max_subflows=2, max_add_addr_accepted=2)

## 3. Configure MPTCP endpoints
# H1 can initiate subflows from its interface  
eth1a.enable_mptcp_endpoint(flags=["subflow"])

# H2 advertises both interfaces - the reliable and wireless-like paths
eth2a.enable_mptcp_endpoint(flags=["signal"])  # Reliable path
eth2b.enable_mptcp_endpoint(flags=["signal"])  # Wireless-like path with loss

print("\nStarting MPTCP experiment with wireless-like conditions...")
print("Expected behavior:")
print("- MPTCP will establish subflows on both paths") 
print("- Path 1 (reliable): Consistent performance")
print("- Path 2 (wireless): Periodic performance degradation due to loss")
print("- MPTCP should adapt and provide better overall throughput than single path")

# Run the experiment with the flow we just created.
exp = Experiment("mptcp-wireless-simulation")
exp.add_mptcp_flow(flow)
exp.run()

print("\nExperiment completed!")
print("Check the experiment dump for:")
print("- Netperf throughput graphs showing path aggregation")  
print("- MPTCP monitor logs showing subflow establishment and behavior")
print("- Socket statistics showing how MPTCP handled lossy conditions")
