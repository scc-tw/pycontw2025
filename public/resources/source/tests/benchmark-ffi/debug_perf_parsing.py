#!/usr/bin/env python3
"""Debug perf stat parsing issues."""

import subprocess
import sys

def debug_parse_perf_output(perf_output: str):
    """Debug version of perf stat parsing."""
    counters = {}
    
    print("=== DEBUGGING PERF OUTPUT PARSING ===")
    print(f"Raw output:")
    print(repr(perf_output))
    print("\n=== LINE BY LINE ANALYSIS ===")
    
    for i, line in enumerate(perf_output.split('\n')):
        print(f"Line {i}: {repr(line)}")
        
        if ',' in line and not line.startswith('#'):
            parts = [p.strip() for p in line.split(',')]
            print(f"  Parts: {parts}")
            print(f"  Parts count: {len(parts)}")
            
            if len(parts) >= 3:
                try:
                    value_str = parts[0]
                    event_name = parts[2] if len(parts) > 2 else 'unknown'
                    
                    print(f"  Value string: '{value_str}'")
                    print(f"  Event name: '{event_name}'")
                    
                    # Handle different value formats
                    if value_str == '<not supported>':
                        print("  → Skipping: not supported")
                        continue
                    elif value_str == '<not counted>':
                        print("  → Skipping: not counted")
                        continue
                    elif not value_str or value_str.isspace():
                        print("  → Skipping: empty value")
                        continue
                    else:
                        # Remove any comma separators in numbers
                        value_str = value_str.replace(',', '')
                        
                        # Skip if value contains non-numeric characters
                        if any(char.isalpha() for char in value_str):
                            print(f"  → Skipping: contains letters: '{value_str}'")
                            continue
                            
                        value = float(value_str)
                        print(f"  → Parsed value: {value}")
                        
                        # Clean event name
                        clean_event_name = event_name
                        if '/' in clean_event_name:
                            if clean_event_name.startswith(('cpu_atom/', 'cpu_core/')):
                                clean_event_name = clean_event_name.split('/')[1]
                                print(f"    → Cleaned event name: '{clean_event_name}'")
                        
                        if clean_event_name in counters:
                            counters[clean_event_name] += value
                            print(f"    → Added to existing: {counters[clean_event_name]}")
                        else:
                            counters[clean_event_name] = value
                            print(f"    → New counter: {value}")
                            
                except (ValueError, IndexError) as e:
                    print(f"  → ERROR: {e}")
                    print(f"    Trying to parse value_str: '{value_str}'")
                    continue
        else:
            print("  → Skipping: no comma or comment line")
    
    print(f"\n=== FINAL COUNTERS ===")
    for name, value in counters.items():
        print(f"{name}: {value}")
    
    return counters

def test_perf_parsing():
    """Test perf parsing with a simple command."""
    events = ['cycles', 'instructions']
    cmd = ['perf', 'stat', '-e', ','.join(events), '--field-separator=,', 'python3', '-c', 'print("test")']
    
    print("Running command:", ' '.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"\nReturn code: {result.returncode}")
    print(f"STDOUT: {repr(result.stdout)}")
    print(f"STDERR: {repr(result.stderr)}")
    
    if result.returncode == 0:
        counters = debug_parse_perf_output(result.stderr)
        print(f"\nParsed {len(counters)} counters successfully!")
    else:
        print("Command failed!")

if __name__ == "__main__":
    test_perf_parsing()