use pyo3::prelude::*;
use std::{fs, thread, time::{Duration, Instant}};

mod core;
use core::*;

// All core functions are now imported from core.rs

/// Get current RSS memory usage in MiB
#[pyfunction]
fn get_rss_mib() -> PyResult<f64> {
    Ok(rss_kib() as f64 / 1024.0)
}

/// Get current RSS memory usage in KiB
#[pyfunction]
fn get_rss_kib() -> PyResult<u64> {
    Ok(rss_kib())
}

/// Run the arena allocation test with specified thread count
/// Returns a tuple of (initial_rss_mib, final_rss_mib)
#[pyfunction]
fn run_arena_test(thread_count: usize) -> PyResult<(f64, f64)> {
    let initial_rss = rss_kib() as f64 / 1024.0;
    
    // Run the task
    task(thread_count);
    
    let final_rss = rss_kib() as f64 / 1024.0;
    
    Ok((initial_rss, final_rss))
}

/// Run the arena allocation test with monitoring
/// Returns a dictionary with detailed information
#[pyfunction]
fn run_arena_test_detailed(thread_count: usize, sleep_seconds: Option<u64>) -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new(py);
        
        let pid = std::process::id();
        let initial_rss = rss_kib() as f64 / 1024.0;
        
        dict.set_item("pid", pid)?;
        dict.set_item("thread_count", thread_count)?;
        dict.set_item("initial_rss_mib", initial_rss)?;
        dict.set_item("allocs_per_thread", ALLOCS_PER_THREAD)?;
        dict.set_item("alloc_size_bytes", ALLOC_SIZE)?;
        
        // Run the task
        task(thread_count);
        
        let after_task_rss = rss_kib() as f64 / 1024.0;
        dict.set_item("after_task_rss_mib", after_task_rss)?;
        
        // Optional sleep to observe memory
        if let Some(sleep_secs) = sleep_seconds {
            thread::sleep(Duration::from_secs(sleep_secs));
            let after_sleep_rss = rss_kib() as f64 / 1024.0;
            dict.set_item("after_sleep_rss_mib", after_sleep_rss)?;
        }
        
        Ok(dict.into())
    })
}

/// Configure the number of allocations per thread (default: 1)
#[pyfunction]
fn set_allocs_per_thread(_allocs: usize) -> PyResult<()> {
    // Note: This would require making ALLOCS_PER_THREAD mutable
    // For now, just return Ok to show the interface
    println!("Note: allocs_per_thread is currently fixed at {}", ALLOCS_PER_THREAD);
    Ok(())
}

/// Get current configuration
#[pyfunction]
fn get_config() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("allocs_per_thread", ALLOCS_PER_THREAD)?;
        dict.set_item("alloc_size_bytes", ALLOC_SIZE)?;
        dict.set_item("alloc_size_mib", ALLOC_SIZE as f64 / (1024.0 * 1024.0))?;
        Ok(dict.into())
    })
}

/// Get comprehensive memory statistics from /proc/self/status
#[pyfunction]
fn get_memory_stats() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let stats = parse_proc_status();
        let dict = pyo3::types::PyDict::new(py);
        
        // Memory values in KB
        dict.set_item("vm_rss_kb", stats.vm_rss_kb)?;
        dict.set_item("vm_peak_kb", stats.vm_peak_kb)?;
        dict.set_item("vm_size_kb", stats.vm_size_kb)?;
        dict.set_item("vm_hwm_kb", stats.vm_hwm_kb)?;
        dict.set_item("vm_data_kb", stats.vm_data_kb)?;
        dict.set_item("vm_stk_kb", stats.vm_stk_kb)?;
        dict.set_item("vm_exe_kb", stats.vm_exe_kb)?;
        dict.set_item("vm_lib_kb", stats.vm_lib_kb)?;
        
        // Memory values in MiB for convenience
        dict.set_item("vm_rss_mib", stats.vm_rss_kb as f64 / 1024.0)?;
        dict.set_item("vm_peak_mib", stats.vm_peak_kb as f64 / 1024.0)?;
        dict.set_item("vm_size_mib", stats.vm_size_kb as f64 / 1024.0)?;
        dict.set_item("vm_hwm_mib", stats.vm_hwm_kb as f64 / 1024.0)?;
        dict.set_item("vm_data_mib", stats.vm_data_kb as f64 / 1024.0)?;
        dict.set_item("vm_stk_mib", stats.vm_stk_kb as f64 / 1024.0)?;
        dict.set_item("vm_exe_mib", stats.vm_exe_kb as f64 / 1024.0)?;
        dict.set_item("vm_lib_mib", stats.vm_lib_kb as f64 / 1024.0)?;
        
        Ok(dict.into())
    })
}

/// Get system and process statistics
#[pyfunction]
fn get_system_stats() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new(py);
        
        dict.set_item("pid", std::process::id())?;
        dict.set_item("thread_count", get_thread_count())?;
        
        // Read some basic system info
        if let Ok(loadavg) = fs::read_to_string("/proc/loadavg") {
            let loads: Vec<&str> = loadavg.split_whitespace().collect();
            if loads.len() >= 3 {
                dict.set_item("load_1min", loads[0].parse::<f64>().unwrap_or(0.0))?;
                dict.set_item("load_5min", loads[1].parse::<f64>().unwrap_or(0.0))?;
                dict.set_item("load_15min", loads[2].parse::<f64>().unwrap_or(0.0))?;
            }
        }
        
        // Memory info from /proc/meminfo
        if let Ok(meminfo) = fs::read_to_string("/proc/meminfo") {
            let mut mem_total = 0u64;
            let mut mem_available = 0u64;
            let mut mem_free = 0u64;
            
            for line in meminfo.lines() {
                if let Some(rest) = line.strip_prefix("MemTotal:") {
                    mem_total = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
                } else if let Some(rest) = line.strip_prefix("MemAvailable:") {
                    mem_available = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
                } else if let Some(rest) = line.strip_prefix("MemFree:") {
                    mem_free = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
                }
            }
            
            dict.set_item("system_mem_total_kb", mem_total)?;
            dict.set_item("system_mem_available_kb", mem_available)?;
            dict.set_item("system_mem_free_kb", mem_free)?;
            dict.set_item("system_mem_total_mib", mem_total as f64 / 1024.0)?;
            dict.set_item("system_mem_available_mib", mem_available as f64 / 1024.0)?;
            dict.set_item("system_mem_free_mib", mem_free as f64 / 1024.0)?;
        }
        
        Ok(dict.into())
    })
}

/// Get combined statistics (memory + system + config)
#[pyfunction]
fn get_all_stats() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new(py);
        
        // Memory stats
        let mem_stats = parse_proc_status();
        let mem_dict = pyo3::types::PyDict::new(py);
        mem_dict.set_item("vm_rss_kb", mem_stats.vm_rss_kb)?;
        mem_dict.set_item("vm_peak_kb", mem_stats.vm_peak_kb)?;
        mem_dict.set_item("vm_size_kb", mem_stats.vm_size_kb)?;
        mem_dict.set_item("vm_hwm_kb", mem_stats.vm_hwm_kb)?;
        mem_dict.set_item("vm_data_kb", mem_stats.vm_data_kb)?;
        mem_dict.set_item("vm_stk_kb", mem_stats.vm_stk_kb)?;
        mem_dict.set_item("vm_exe_kb", mem_stats.vm_exe_kb)?;
        mem_dict.set_item("vm_lib_kb", mem_stats.vm_lib_kb)?;
        mem_dict.set_item("vm_rss_mib", mem_stats.vm_rss_kb as f64 / 1024.0)?;
        mem_dict.set_item("vm_peak_mib", mem_stats.vm_peak_kb as f64 / 1024.0)?;
        dict.set_item("memory", mem_dict)?;
        
        // System stats
        dict.set_item("pid", std::process::id())?;
        dict.set_item("thread_count", get_thread_count())?;
        
        // Config
        let config_dict = pyo3::types::PyDict::new(py);
        config_dict.set_item("allocs_per_thread", ALLOCS_PER_THREAD)?;
        config_dict.set_item("alloc_size_bytes", ALLOC_SIZE)?;
        config_dict.set_item("alloc_size_mib", ALLOC_SIZE as f64 / (1024.0 * 1024.0))?;
        dict.set_item("config", config_dict)?;
        
        // Timestamp
        dict.set_item("timestamp", std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64())?;
        
        Ok(dict.into())
    })
}

/// Monitor memory usage over time and return a list of snapshots
#[pyfunction]
fn monitor_memory(duration_seconds: f64, interval_seconds: f64) -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let snapshots = pyo3::types::PyList::empty(py);
        let start_time = Instant::now();
        let duration = Duration::from_secs_f64(duration_seconds);
        let interval = Duration::from_secs_f64(interval_seconds);
        
        while start_time.elapsed() < duration {
            let snapshot = pyo3::types::PyDict::new(py);
            let mem_stats = parse_proc_status();
            let elapsed = start_time.elapsed().as_secs_f64();
            
            snapshot.set_item("elapsed_seconds", elapsed)?;
            snapshot.set_item("vm_rss_mib", mem_stats.vm_rss_kb as f64 / 1024.0)?;
            snapshot.set_item("vm_peak_mib", mem_stats.vm_peak_kb as f64 / 1024.0)?;
            snapshot.set_item("vm_size_mib", mem_stats.vm_size_kb as f64 / 1024.0)?;
            snapshot.set_item("thread_count", get_thread_count())?;
            
            snapshots.append(snapshot)?;
            thread::sleep(interval);
        }
        
        Ok(snapshots.into())
    })
}

/// A Python module implemented in Rust for glibc arena testing
#[pymodule]
fn glibc_arena_poc(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Basic arena test functions
    m.add_function(wrap_pyfunction!(get_rss_mib, m)?)?;
    m.add_function(wrap_pyfunction!(get_rss_kib, m)?)?;
    m.add_function(wrap_pyfunction!(run_arena_test, m)?)?;
    m.add_function(wrap_pyfunction!(run_arena_test_detailed, m)?)?;
    m.add_function(wrap_pyfunction!(set_allocs_per_thread, m)?)?;
    m.add_function(wrap_pyfunction!(get_config, m)?)?;
    
    // Statistics and monitoring functions
    m.add_function(wrap_pyfunction!(get_memory_stats, m)?)?;
    m.add_function(wrap_pyfunction!(get_system_stats, m)?)?;
    m.add_function(wrap_pyfunction!(get_all_stats, m)?)?;
    m.add_function(wrap_pyfunction!(monitor_memory, m)?)?;
    
    // Module-level constants
    m.add("DEFAULT_THREAD_COUNT", DEFAULT_THREAD_COUNT)?;
    m.add("ALLOC_SIZE_BYTES", ALLOC_SIZE)?;
    m.add("ALLOC_SIZE_MIB", ALLOC_SIZE as f64 / (1024.0 * 1024.0))?;
    
    Ok(())
}
