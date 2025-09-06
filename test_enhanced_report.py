#!/usr/bin/env python3

"""
Test Enhanced MPTCP Analysis Report Generator

This script tests the enhanced MPTCP report generator with topology diagrams
and subflow capacity analysis features.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_mptcp_analysis_report import MPTCPAnalysisReport

def create_mock_experiment_data():
    """Create mock experiment data for testing"""
    
    # Create temporary directory structure
    temp_base = tempfile.mkdtemp(prefix="mptcp_test_")
    
    # Create mock experiment directories
    experiments = {
        "mptcp_default_dump_20240101_120000": {
            "topology": "default",
            "flow_count": 2
        },
        "mptcp_wireless_dump_20240101_130000": {
            "topology": "wireless", 
            "flow_count": 2
        },
        "mptcp_mega_dumbbell_dump_20240101_140000": {
            "topology": "mega_dumbbell",
            "flow_count": 1
        }
    }
    
    for exp_name, exp_data in experiments.items():
        exp_dir = os.path.join(temp_base, exp_name)
        os.makedirs(exp_dir, exist_ok=True)
        
        # Create mock flow data files
        for flow_file in exp_data["flow_files"]:
            flow_path = os.path.join(exp_dir, flow_file)
            with open(flow_path, 'w') as f:
                # Simulate netperf output for default topology
                if "default" in exp_name:
                    if "flow_1" in flow_file:
                        f.write("# Mock netperf output for Flow 1\n")
                        for i in range(10):
                            f.write(f"1.{i:02d} {4.8 + i * 0.1:.2f}\n")  # ~5 Mbps
                    else:
                        f.write("# Mock netperf output for Flow 2\n")
                        for i in range(10):
                            f.write(f"1.{i:02d} {4.5 + i * 0.15:.2f}\n")  # ~5 Mbps
                
                # Simulate netperf output for wireless topology
                elif "wireless" in exp_name:
                    if "flow_1" in flow_file:
                        f.write("# Mock netperf output for Flow 1 (Reliable path)\n")
                        for i in range(10):
                            f.write(f"1.{i:02d} {9.5 + i * 0.05:.2f}\n")  # ~10 Mbps
                    else:
                        f.write("# Mock netperf output for Flow 2 (Wireless path)\n")
                        # Simulate wireless variability
                        for i in range(10):
                            if i % 3 == 0:  # Packet loss periods
                                f.write(f"1.{i:02d} {2.0 + i * 0.1:.2f}\n")  # Reduced throughput
                            else:
                                f.write(f"1.{i:02d} {7.5 + i * 0.1:.2f}\n")  # ~8 Mbps
                
                # Simulate netperf output for mega dumbbell
                else:  # mega dumbbell
                    f.write("# Mock netperf output for Mega Dumbbell\n")
                    for i in range(10):
                        f.write(f"1.{i:02d} {18.5 + i * 0.2:.2f}\n")  # ~20 Mbps aggregated
        
        # Create mock monitor files
        for monitor_file in exp_data["monitor_files"]:
            monitor_path = os.path.join(exp_dir, monitor_file)
            with open(monitor_path, 'w') as f:
                if "mptcp_monitor" in monitor_file:
                    f.write("# Mock MPTCP monitor output\n")
                    f.write("Time: 1.00s, Subflows: 2, Connections: 1\n")
                    f.write("Subflow 1: 192.168.1.1:5001 -> 192.168.2.1:12345, State: ESTABLISHED\n")
                    f.write("Subflow 2: 192.168.3.1:5001 -> 192.168.4.1:12346, State: ESTABLISHED\n")
                    f.write("Time: 2.00s, Subflows: 2, Connections: 1\n")
                    f.write("Subflow 1: 192.168.1.1:5001 -> 192.168.2.1:12345, State: ESTABLISHED\n")
                    f.write("Subflow 2: 192.168.3.1:5001 -> 192.168.4.1:12346, State: ESTABLISHED\n")
                elif "ss_monitor" in monitor_file:
                    f.write("# Mock ss output\n")
                    f.write("State Recv-Q Send-Q Local:Port Peer:Port\n")
                    f.write("ESTAB 0 0 192.168.1.1:5001 192.168.2.1:12345\n")
                    f.write("ESTAB 0 0 192.168.3.1:5001 192.168.4.1:12346\n")
    
    return temp_base

def test_topology_analysis():
    """Test topology determination and analysis"""
    print("🧪 Testing topology analysis...")
    
    generator = MPTCPAnalysisReport()
    
    # Test different experiment name patterns
    test_cases = [
        ("mptcp_default_dump_test", "Default Dual Path"),
        ("mptcp_wireless_experiment", "Wireless-like Dual Path"),
        ("mptcp_mega_dumbbell_test", "Mega Dumbbell"),
        ("unknown_experiment", "Default Dual Path")  # Fallback
    ]
    
    for exp_name, expected_type in test_cases:
        topology_info = generator.determine_topology_type(exp_name)
        print(f"  ✓ {exp_name} -> {topology_info['type']}")
        assert topology_info['type'] == expected_type, f"Expected {expected_type}, got {topology_info['type']}"
        assert 'theoretical_max' in topology_info
        assert 'paths' in topology_info
        assert len(topology_info['paths']) >= 1

def test_subflow_analysis():
    """Test subflow capacity analysis"""
    print("🧪 Testing subflow capacity analysis...")
    
    generator = MPTCPAnalysisReport()
    
    # Mock flow statistics
    mock_flow_stats = [
        {'avg_throughput': 4.8, 'min_throughput': 4.5, 'max_throughput': 5.2},
        {'avg_throughput': 4.2, 'min_throughput': 3.8, 'max_throughput': 4.8}
    ]
    
    analysis = generator.analyze_subflow_capacities("mptcp_default_test", mock_flow_stats)
    
    print(f"  ✓ Theoretical capacity: {analysis['theoretical_capacity']} Mbps")
    print(f"  ✓ Actual throughput: {analysis['actual_throughput']:.2f} Mbps")
    print(f"  ✓ Aggregation efficiency: {analysis['aggregation_efficiency']:.1f}%")
    print(f"  ✓ Subflows analyzed: {len(analysis['subflow_breakdown'])}")
    
    assert analysis['theoretical_capacity'] > 0
    assert analysis['actual_throughput'] > 0
    assert len(analysis['subflow_breakdown']) == 2

def test_visualization_creation():
    """Test topology diagram and subflow analysis chart creation"""
    print("🧪 Testing visualization creation...")
    
    generator = MPTCPAnalysisReport()
    
    # Test topology diagram creation
    topology_info = generator.determine_topology_type("mptcp_default_test")
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        topology_path = tmp_file.name
    
    try:
        result_path = generator.create_topology_diagram(topology_info, topology_path)
        assert os.path.exists(result_path)
        print(f"  ✓ Topology diagram created: {result_path}")
    finally:
        if os.path.exists(topology_path):
            os.unlink(topology_path)
    
    # Test subflow analysis chart creation
    mock_flow_stats = [
        {'avg_throughput': 4.8, 'min_throughput': 4.5, 'max_throughput': 5.2},
        {'avg_throughput': 4.2, 'min_throughput': 3.8, 'max_throughput': 4.8}
    ]
    
    analysis = generator.analyze_subflow_capacities("mptcp_default_test", mock_flow_stats)
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        chart_path = tmp_file.name
    
    try:
        result_path = generator.create_subflow_analysis_chart(analysis, chart_path)
        assert os.path.exists(result_path)
        print(f"  ✓ Subflow analysis chart created: {result_path}")
    finally:
        if os.path.exists(chart_path):
            os.unlink(chart_path)

def test_full_report_generation():
    """Test complete enhanced report generation"""
    print("🧪 Testing full enhanced report generation...")
    
    # Create mock experiment data
    temp_dir = create_mock_experiment_data()
    
    try:
        # Change to temporary directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        generator = MPTCPAnalysisReport()
        
        # Generate the enhanced report
        report_path = generator.generate_pdf_report("Test_Enhanced_MPTCP_Report.pdf")
        
        if report_path and os.path.exists(report_path):
            print(f"  ✅ Enhanced report generated successfully: {report_path}")
            print(f"  📄 Report size: {os.path.getsize(report_path) / 1024:.1f} KB")
            
            # Copy report to original directory for inspection
            final_report_path = os.path.join(original_cwd, "Test_Enhanced_MPTCP_Report.pdf")
            shutil.copy2(report_path, final_report_path)
            print(f"  📋 Report copied to: {final_report_path}")
            
            return True
        else:
            print("  ❌ Report generation failed")
            return False
    
    finally:
        # Clean up
        os.chdir(original_cwd)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def main():
    """Main test function"""
    print("🚀 Testing Enhanced MPTCP Analysis Report Generator")
    print("=" * 60)
    
    try:
        # Run individual component tests
        test_topology_analysis()
        print()
        
        test_subflow_analysis()
        print()
        
        test_visualization_creation()
        print()
        
        # Run full integration test
        success = test_full_report_generation()
        
        print()
        print("=" * 60)
        if success:
            print("🎉 All tests passed! Enhanced report generator is working correctly.")
            print("📊 The enhanced report now includes:")
            print("  • Network topology diagrams")
            print("  • Subflow capacity analysis charts") 
            print("  • Aggregation efficiency metrics")
            print("  • Bottleneck identification")
            print("  • Comprehensive topology-aware analysis")
        else:
            print("❌ Some tests failed. Check the output above for details.")
            return 1
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
