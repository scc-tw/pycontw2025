// Core functionality shared between main.rs and lib.rs
use std::{fs, thread, time::{Duration, Instant}};

pub const DEFAULT_THREAD_COUNT: usize = 1280000;
pub const ALLOCS_PER_THREAD: usize = 1;
pub const ALLOC_SIZE: usize = 64 * 1024 * 1024;   // 64 MiB

#[derive(Debug, Clone)]
pub struct MemoryStats {
    pub vm_rss_kb: u64,
    pub vm_peak_kb: u64,
    pub vm_size_kb: u64,
    pub vm_hwm_kb: u64,
    pub vm_data_kb: u64,
    pub vm_stk_kb: u64,
    pub vm_exe_kb: u64,
    pub vm_lib_kb: u64,
}

impl MemoryStats {
    pub fn vm_rss_mib(&self) -> f64 {
        self.vm_rss_kb as f64 / 1024.0
    }
    
    pub fn vm_peak_mib(&self) -> f64 {
        self.vm_peak_kb as f64 / 1024.0
    }
}

pub fn rss_kib() -> u64 {
    // Read VmRSS from /proc/self/status (kB)
    let s = fs::read_to_string("/proc/self/status").unwrap_or_default();
    for line in s.lines() {
        if let Some(rest) = line.strip_prefix("VmRSS:") {
            return rest.split_whitespace().next().unwrap_or("0").parse::<u64>().unwrap_or(0);
        }
    }
    0
}

pub fn parse_proc_status() -> MemoryStats {
    let s = fs::read_to_string("/proc/self/status").unwrap_or_default();
    let mut stats = MemoryStats {
        vm_rss_kb: 0,
        vm_peak_kb: 0,
        vm_size_kb: 0,
        vm_hwm_kb: 0,
        vm_data_kb: 0,
        vm_stk_kb: 0,
        vm_exe_kb: 0,
        vm_lib_kb: 0,
    };
    
    for line in s.lines() {
        if let Some(rest) = line.strip_prefix("VmRSS:") {
            stats.vm_rss_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        } else if let Some(rest) = line.strip_prefix("VmPeak:") {
            stats.vm_peak_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        } else if let Some(rest) = line.strip_prefix("VmSize:") {
            stats.vm_size_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        } else if let Some(rest) = line.strip_prefix("VmHWM:") {
            stats.vm_hwm_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        } else if let Some(rest) = line.strip_prefix("VmData:") {
            stats.vm_data_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        } else if let Some(rest) = line.strip_prefix("VmStk:") {
            stats.vm_stk_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        } else if let Some(rest) = line.strip_prefix("VmExe:") {
            stats.vm_exe_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        } else if let Some(rest) = line.strip_prefix("VmLib:") {
            stats.vm_lib_kb = rest.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
        }
    }
    
    stats
}

pub fn get_thread_count() -> usize {
    // Count threads by reading /proc/self/stat
    if let Ok(stat) = fs::read_to_string("/proc/self/stat") {
        if let Some(thread_count_str) = stat.split_whitespace().nth(19) {
            return thread_count_str.parse().unwrap_or(1);
        }
    }
    1
}

pub fn worker() {
    for _ in 0..ALLOCS_PER_THREAD {
        let mut v = Vec::<u8>::with_capacity(ALLOC_SIZE);
        unsafe { v.set_len(ALLOC_SIZE); }
        drop(v);
    }
}

pub fn task(thread_count: usize) {
    let mut ths = Vec::with_capacity(thread_count);
    for _ in 0..thread_count {
        ths.push(thread::spawn(worker));
    }
    for th in ths {
        th.join().unwrap();
    }
}

pub fn print_rss(tag: &str) {
    println!("[{tag}] RSS = {:.2} MiB", rss_kib() as f64 / 1024.0);
}

#[derive(Debug)]
pub struct ArenaTestResult {
    pub initial_rss_mib: f64,
    pub final_rss_mib: f64,
    pub difference_mib: f64,
    pub thread_count: usize,
    pub duration_secs: f64,
}

impl ArenaTestResult {
    pub fn new(initial_rss_mib: f64, final_rss_mib: f64, thread_count: usize, duration_secs: f64) -> Self {
        Self {
            initial_rss_mib,
            final_rss_mib,
            difference_mib: final_rss_mib - initial_rss_mib,
            thread_count,
            duration_secs,
        }
    }
}

pub fn run_arena_test_with_timing(thread_count: usize) -> ArenaTestResult {
    let start_time = Instant::now();
    let initial_rss = rss_kib() as f64 / 1024.0;
    
    task(thread_count);
    
    let final_rss = rss_kib() as f64 / 1024.0;
    let duration = start_time.elapsed().as_secs_f64();
    
    ArenaTestResult::new(initial_rss, final_rss, thread_count, duration)
}
