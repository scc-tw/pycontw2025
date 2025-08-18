use std::{env, thread, time::Duration};
use std::io::{self, Read};

mod core;
use core::*;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    let thread_count = if args.len() > 1 {
        args[1].parse::<usize>().unwrap_or_else(|_| {
            DEFAULT_THREAD_COUNT
        })
    } else {
        DEFAULT_THREAD_COUNT
    };

    println!("=== Glibc Arena Memory Leak Test ===");
    let pid = std::process::id();
    println!("PID: {}", pid);
    println!("Thread count: {}", thread_count);
    println!("Allocations per thread: {}", ALLOCS_PER_THREAD);
    println!("Allocation size: {:.1} MiB ({} bytes)", ALLOC_SIZE as f64 / (1024.0 * 1024.0), ALLOC_SIZE);
    
    println!("\nMonitoring commands:");
    println!("  watch -n0.5 pmap -x {}", pid);
    println!("  top -p {}", pid);
    
    println!("\nPress ENTER to start the test...");
    let _ = io::stdin().read(&mut [0u8]).ok();

    // Run the test with timing
    println!("\nRunning arena allocation test...");
    let result = run_arena_test_with_timing(thread_count);
    
    println!("\n=== Test Results ===");
    println!("Thread count: {}", result.thread_count);
    println!("Duration: {:.2} seconds", result.duration_secs);
    println!("Initial RSS: {:.2} MiB", result.initial_rss_mib);
    println!("Final RSS: {:.2} MiB", result.final_rss_mib);
    println!("Memory difference: {:.2} MiB", result.difference_mib);
    
    if result.difference_mib > 0.0 {
        println!("\n⚠️  Memory increased by {:.2} MiB - potential arena leak detected!", result.difference_mib);
    } else {
        println!("\n✅ No significant memory increase detected.");
    }

    println!("\nAllocations done. Memory may still appear >0 due to per-thread arenas.");
    
    // Show additional stats
    let mem_stats = parse_proc_status();
    println!("\n=== Detailed Memory Stats ===");
    println!("VmRSS (current): {:.2} MiB", mem_stats.vm_rss_mib());
    println!("VmPeak (peak): {:.2} MiB", mem_stats.vm_peak_mib());
    println!("VmSize (virtual): {:.2} MiB", mem_stats.vm_size_kb as f64 / 1024.0);
    println!("VmData (data): {:.2} MiB", mem_stats.vm_data_kb as f64 / 1024.0);

    println!("\nSleeping for 5 minutes so you can watch memory usage...");
    thread::sleep(Duration::from_secs(300));
    
    // Final stats
    let final_stats = parse_proc_status();
    println!("\n=== Final Memory Stats ===");
    println!("Final RSS: {:.2} MiB", final_stats.vm_rss_mib());
    println!("Peak RSS: {:.2} MiB", final_stats.vm_peak_mib());
}
