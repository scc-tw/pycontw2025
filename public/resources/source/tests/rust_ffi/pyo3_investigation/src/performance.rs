// pyo3_investigation/src/performance.rs
// Performance comparison benchmarks between PyO3 and handcrafted FFI

use pyo3::prelude::*;
use std::time::Instant;
use std::collections::HashMap;
use crate::bug_4627::TestSubclass;

#[pyfunction]
pub fn pyo3_function_call_test() -> i32 {
    42
}

#[pyfunction]
pub fn pyo3_string_conversion_test(input: String) -> String {
    format!("PyO3 processed: {}", input)
}

#[pyfunction]
pub fn benchmark_pyo3_overhead() -> PyResult<Vec<(String, f64)>> {
    let mut results = Vec::new();
    let iterations = 100_000;
    
    // Basic function call benchmark
    let start = Instant::now();
    for _ in 0..iterations {
        pyo3_function_call_test();
    }
    let duration = start.elapsed().as_nanos() as f64 / iterations as f64;
    results.push(("pyo3_function_call_ns".to_string(), duration));
    
    // String conversion benchmark
    let test_string = "test string for conversion".to_string();
    let start = Instant::now();
    for _ in 0..iterations {
        pyo3_string_conversion_test(test_string.clone());
    }
    let duration = start.elapsed().as_nanos() as f64 / iterations as f64;
    results.push(("pyo3_string_conversion_ns".to_string(), duration));
    
    Ok(results)
}

#[pyfunction]
pub fn memory_allocation_benchmark() -> PyResult<HashMap<String, f64>> {
    let mut results = HashMap::new();
    let iterations = 10_000;
    
    // PyO3 object creation
    let start = Instant::now();
    let mut objects = Vec::new();
    for i in 0..iterations {
        let obj = TestSubclass::new(format!("bench_{}", i), i as u64);
        objects.push(obj);
    }
    let creation_time = start.elapsed().as_nanos() as f64 / iterations as f64;
    results.insert("pyo3_object_creation_ns".to_string(), creation_time);
    
    // Cleanup measurement
    let start = Instant::now();
    drop(objects);
    let cleanup_time = start.elapsed().as_nanos() as f64 / iterations as f64;
    results.insert("pyo3_object_cleanup_ns".to_string(), cleanup_time);
    
    Ok(results)
}

#[pyfunction]
pub fn benchmark_string_operations(input: String, iterations: usize) -> PyResult<HashMap<String, f64>> {
    let mut results = HashMap::new();
    
    // String processing benchmark
    let start = Instant::now();
    for _ in 0..iterations {
        let processed = format!("PyO3 processed: {}", input);
        let reversed: String = processed.chars().rev().collect();
        let _final = format!("Final: {}", reversed);
    }
    let string_time = start.elapsed().as_nanos() as f64 / iterations as f64;
    results.insert("pyo3_string_ops_ns".to_string(), string_time);
    
    Ok(results)
}

#[pyfunction]
pub fn benchmark_callback_performance() -> PyResult<HashMap<String, f64>> {
    let mut results = HashMap::new();
    let iterations = 1_000;
    
    Python::with_gil(|py| -> PyResult<()> {
        // Create a simple callable that simulates callback overhead
        let builtins = py.import_bound("builtins")?;
        let test_callback = builtins.getattr("abs")?;  // Use built-in function for callback testing
        
        // Benchmark callback execution
        let start = Instant::now();
        for i in 0..iterations {
            let arg = (i % 100) as i32;
            let _result = test_callback.call1((arg,))?;
        }
        let callback_time = start.elapsed().as_nanos() as f64 / iterations as f64;
        results.insert("pyo3_callback_ns".to_string(), callback_time);
        
        Ok(())
    })?;
    
    Ok(results)
}

#[pyfunction]
pub fn benchmark_gil_acquisition() -> PyResult<HashMap<String, f64>> {
    let mut results = HashMap::new();
    let iterations = 10_000;
    
    // Benchmark GIL acquisition overhead
    let start = Instant::now();
    for _ in 0..iterations {
        Python::with_gil(|_py| {
            // Minimal work inside GIL
            let _x = 42;
        });
    }
    let gil_time = start.elapsed().as_nanos() as f64 / iterations as f64;
    results.insert("pyo3_gil_acquisition_ns".to_string(), gil_time);
    
    Ok(results)
}

#[pyfunction]
pub fn comprehensive_benchmark_suite() -> PyResult<HashMap<String, HashMap<String, f64>>> {
    let mut suite_results = HashMap::new();
    
    // Run all benchmark categories
    let function_results = benchmark_pyo3_overhead()?;
    let mut function_map = HashMap::new();
    for (key, value) in function_results {
        function_map.insert(key, value);
    }
    suite_results.insert("function_calls".to_string(), function_map);
    
    suite_results.insert("memory_allocation".to_string(), memory_allocation_benchmark()?);
    suite_results.insert("string_operations".to_string(), benchmark_string_operations("test".to_string(), 10000)?);
    suite_results.insert("callback_performance".to_string(), benchmark_callback_performance()?);
    suite_results.insert("gil_acquisition".to_string(), benchmark_gil_acquisition()?);
    
    Ok(suite_results)
}