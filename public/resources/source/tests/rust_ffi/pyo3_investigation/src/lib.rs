// pyo3_investigation/src/lib.rs
// PyO3 bug reproduction and investigation module

use pyo3::prelude::*;
use std::collections::HashMap;

// Basic PyO3 test functions for performance comparison
#[pyfunction]
fn pyo3_function_call_test() -> i32 {
    42
}

#[pyfunction]
fn pyo3_string_conversion_test(input: String) -> String {
    format!("PyO3 processed: {}", input)
}

#[pyfunction]
fn create_test_object(size: usize) -> PyResult<HashMap<String, usize>> {
    let mut result = HashMap::new();
    result.insert("size".to_string(), size);
    result.insert("id".to_string(), std::ptr::addr_of!(result) as usize);
    Ok(result)
}

// Module declarations
mod bug_4882;
mod bug_4627;
mod performance;

// Python module definition
#[pymodule]
fn pyo3_investigation(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    // Basic test functions
    m.add_function(wrap_pyfunction!(pyo3_function_call_test, m)?)?;
    m.add_function(wrap_pyfunction!(pyo3_string_conversion_test, m)?)?;
    m.add_function(wrap_pyfunction!(create_test_object, m)?)?;
    
    // Bug reproduction functions
    m.add_function(wrap_pyfunction!(bug_4882::test_abi_cache_poisoning, m)?)?;
    m.add_function(wrap_pyfunction!(bug_4882::demonstrate_build_cache_corruption, m)?)?;
    
    m.add_function(wrap_pyfunction!(bug_4627::reproduce_subclass_gc_flakiness, m)?)?;
    m.add_function(wrap_pyfunction!(bug_4627::stress_test_subclass_lifecycle, m)?)?;
    
    // Performance benchmarks
    m.add_function(wrap_pyfunction!(performance::benchmark_pyo3_overhead, m)?)?;
    m.add_function(wrap_pyfunction!(performance::memory_allocation_benchmark, m)?)?;
    
    // Add subclass for testing
    m.add_class::<bug_4627::TestSubclass>()?;
    
    Ok(())
}