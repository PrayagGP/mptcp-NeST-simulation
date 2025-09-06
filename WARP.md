# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is an MPTCP (Multipath TCP) research project using **NeST (Network Stack Tester)**, a Python 3 network emulation framework. The project focuses on studying MPTCP performance characteristics through network simulations and analysis.

### Key Project Context
- **Primary Purpose**: MPTCP performance analysis and network emulation research
- **NeST Version**: 0.4.4 
- **Language**: Python 3.6+ (requires root access for network namespace operations)
- **Main Components**: Network topology creation, MPTCP experiments, performance analysis
- **Generated Outputs**: Throughput graphs, congestion control analysis, network latency measurements

## Repository Structure

```
nest-mptcp-project/
├── nest/                           # NeST framework (cloned from GitLab)
│   ├── nest/                       # Core NeST Python package
│   │   ├── topology/               # Network topology creation APIs
│   │   ├── experiment/             # Network experiment execution
│   │   ├── engine/                 # Low-level network namespace operations
│   │   └── tests/                  # Unit tests
│   ├── examples/                   # Example scripts and tutorials
│   │   ├── mptcp/                  # MPTCP-specific examples
│   │   └── tcp/                    # Regular TCP examples
│   └── docs/                       # Documentation and API reference
├── venv/                           # Python virtual environment
├── mptcp-graph-analysis.md         # Analysis of simulation results
└── mptcp-simulation-results-summary.md  # Summary of MPTCP experiments
```

## Architecture Overview

### Core NeST Components

**Topology Module** (`nest.topology`)
- **Node**: Base abstraction for network hosts/devices (supports MPTCP)
- **Router**: Network routing devices with IP forwarding enabled  
- **Switch**: Layer 2 switching devices
- **Interface**: Network interface connections between devices
- **Address/Subnet**: IP addressing and network management

**Experiment Module** (`nest.experiment`)
- **Experiment**: Main controller for running network experiments
- **Flow**: Traffic flow definition between nodes
- **Application**: Network applications (HTTP, CoAP, MPEG-DASH, SIP)
- **Parser/Plotter**: Results analysis and visualization

**Engine Module** (`nest.engine`) 
- Low-level network namespace creation and management
- Interface manipulation and traffic control
- System-level networking operations (requires root)

### MPTCP-Specific Architecture

**MPTCP Node Features**:
- Multi-homed node support (multiple IP addresses)
- MPTCP sysctl configuration management
- Subflow monitoring and endpoint management
- MPTCP-specific routing and path management

**Experiment Flow**:
1. Create network topology with multi-homed nodes
2. Configure MPTCP parameters and endpoints
3. Run traffic experiments with netperf/iperf
4. Monitor MPTCP connection state and subflow behavior
5. Generate performance graphs and analysis

## Common Development Commands

### Environment Setup
```bash
# Install NeST in development mode (in nest/ directory)
sudo pip install -e .

# Install development dependencies
pip install pre-commit gitlint
pre-commit install
gitlint install-hook
```

### Testing and Quality Assurance
```bash
# Run all unit tests (requires root)
sudo python3 -m unittest -v

# Run tests with coverage
sudo coverage run
sudo coverage report

# Run style checks (black formatter + pylint)
pre-commit run --all-files

# Check specific files with pylint (must score 10/10)
pylint nest/

# Check commit messages
gitlint --commits origin/master..HEAD
```

### MPTCP Experiment Execution
```bash
# Run specific MPTCP examples (requires root)
sudo python3 nest/examples/mptcp/mptcp-default-configuration.py
sudo python3 nest/examples/mptcp/mptcp-mega-dumbbell.py

# Run with Python virtual environment
source venv/bin/activate
sudo venv/bin/python nest/examples/mptcp/mptcp-helper.py
```

### Development Workflow
```bash
# Format code with black
black nest/

# Run single test file  
sudo python3 -m pytest nest/tests/test_specific.py -v

# Generate documentation
make -C nest/docs html

# Build Docker container for testing
docker-compose build test
```

## Key Development Guidelines

### Code Standards
- **Formatter**: Black (with rare `# fmt: off/on` exceptions)
- **Linter**: Pylint with strict 10/10 score requirement
- **Style**: NumPy docstring format, PEP-8 compliance
- **Testing**: Comprehensive unit tests, coverage reporting

### MPTCP Development Focus
- All network nodes default to MPTCP-enabled (`node.is_mptcp = True`)
- Multi-homed topology creation is standard practice
- MPTCP validation checklist must pass for experiments
- Performance analysis focuses on subflow behavior and throughput aggregation

### Commit Convention
```
<directory>: Commit message in present tense

Detailed description of changes

Signed-off-by: Name <email>
```

### Important Notes
- **Root Access Required**: All NeST operations require sudo/root privileges
- **Network Namespaces**: Core functionality relies on Linux network namespace isolation
- **MPTCP Dependencies**: Requires mptcpize tool and kernel MPTCP support
- **Performance Analysis**: Generated graphs and logs are stored in timestamped directories

## Project-Specific Context

### Research Goals
This project investigates MPTCP performance characteristics through controlled network emulation, focusing on:
- Throughput aggregation across multiple network paths
- Congestion control behavior in multipath scenarios  
- Network latency impact on MPTCP subflow selection
- Complex topology performance (dumbbell networks)

### Key Findings from Current Analysis
- MPTCP successfully provides 20+ Mbps throughput with path aggregation
- Multiple subflows established and managed independently
- Peak performance reaches 70+ Mbps in optimal conditions
- Effective congestion control per subflow with coupled overall management

When working on this codebase, prioritize understanding the MPTCP research context and ensure all network experiments properly validate multipath TCP functionality.
