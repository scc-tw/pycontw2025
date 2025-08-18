// pyo3_investigation/src/bug_4627.rs
// Bug #4627: Subclass + GC flakiness under free-threaded Python

use pyo3::prelude::*;
use std::sync::{Arc, Mutex};
use std::thread;
use std::collections::HashMap;

#[pyclass]
pub struct TestSubclass {
    data: String,
    id: u64,
}

#[pymethods]
impl TestSubclass {
    #[new]
    pub fn new(data: String, id: u64) -> Self {
        TestSubclass { data, id }
    }
    
    pub fn get_data(&self) -> String {
        self.data.clone()
    }
    
    pub fn set_data(&mut self, data: String) {
        self.data = data;
    }
    
    pub fn test_method(&self) -> String {
        format!("TestSubclass {} with data: {}", self.id, self.data)
    }
    
    fn __del__(&mut self) {
        // Destructor that might interact poorly with GC
        println!("Deleting TestSubclass {}", self.id);
    }
}

#[pyfunction]
pub fn create_test_subclass(data: String) -> PyResult<TestSubclass> {
    let id = std::ptr::addr_of!(data) as u64; // Simple ID generation
    Ok(TestSubclass::new(data, id))
}

#[pyfunction]
pub fn reproduce_subclass_gc_flakiness() -> PyResult<Vec<String>> {
    let mut errors = Vec::new();
    let thread_count = 4;
    let objects_per_thread = 500;
    let shared_errors = Arc::new(Mutex::new(Vec::new()));
    
    let mut handles = Vec::new();
    
    for thread_id in 0..thread_count {
        let errors_clone = Arc::clone(&shared_errors);
        
        let handle = thread::spawn(move || {
            Python::with_gil(|py| {
                let mut objects = Vec::new();
                
                for i in 0..objects_per_thread {
                    // Create subclass instances
                    let obj = Py::new(py, TestSubclass::new(
                        format!("data_{}_{}", thread_id, i),
                        (thread_id * 1000 + i) as u64,
                    ));
                    
                    match obj {
                        Ok(py_obj) => {
                            objects.push(py_obj);
                            
                            // Periodically force garbage collection
                            if i % 50 == 0 {
                                if let Err(e) = py.import_bound("gc").and_then(|gc| gc.call_method0("collect")) {
                                    if let Ok(mut errs) = errors_clone.lock() {
                                        errs.push(format!("GC error in thread {}: {}", thread_id, e));
                                    }
                                }
                                
                                // Try to access some objects after GC
                                for (idx, obj) in objects.iter().enumerate().take(10) {
                                    if let Err(e) = obj.call_method0(py, "get_data") {
                                        if let Ok(mut errs) = errors_clone.lock() {
                                            errs.push(format!(
                                                "Object access error after GC in thread {}, obj {}: {}",
                                                thread_id, idx, e
                                            ));
                                        }
                                    }
                                }
                            }
                        }
                        Err(e) => {
                            if let Ok(mut errs) = errors_clone.lock() {
                                errs.push(format!("Object creation error in thread {}: {}", thread_id, e));
                            }
                        }
                    }
                }
                
                // Final GC pass
                if let Err(e) = py.import_bound("gc").and_then(|gc| gc.call_method0("collect")) {
                    if let Ok(mut errs) = errors_clone.lock() {
                        errs.push(format!("Final GC error in thread {}: {}", thread_id, e));
                    }
                }
            });
        });
        
        handles.push(handle);
    }
    
    // Wait for all threads
    for handle in handles {
        handle.join().unwrap();
    }
    
    // Collect all errors
    if let Ok(shared_errs) = shared_errors.lock() {
        errors.extend(shared_errs.clone());
    }
    
    Ok(errors)
}

#[pyfunction]
pub fn stress_test_subclass_lifecycle() -> PyResult<HashMap<String, u32>> {
    let mut stats = HashMap::new();
    stats.insert("objects_created".to_string(), 0);
    stats.insert("gc_runs".to_string(), 0);
    stats.insert("access_errors".to_string(), 0);
    stats.insert("creation_errors".to_string(), 0);
    
    Python::with_gil(|py| {
        for round in 0..100 {
            let mut objects = Vec::new();
            
            // Create many objects
            for i in 0..1000 {
                match Py::new(py, TestSubclass::new(
                    format!("stress_test_{}_{}", round, i),
                    (round * 1000 + i) as u64,
                )) {
                    Ok(obj) => {
                        objects.push(obj);
                        *stats.get_mut("objects_created").unwrap() += 1;
                    }
                    Err(_) => {
                        *stats.get_mut("creation_errors").unwrap() += 1;
                    }
                }
            }
            
            // Force GC multiple times
            for _ in 0..5 {
                match py.import_bound("gc").and_then(|gc| gc.call_method0("collect")) {
                    Ok(_) => {
                        *stats.get_mut("gc_runs").unwrap() += 1;
                    }
                    Err(_) => {
                        // GC error
                    }
                }
                
                // Try to access random objects
                for obj in objects.iter().step_by(100) {
                    if obj.call_method0(py, "get_data").is_err() {
                        *stats.get_mut("access_errors").unwrap() += 1;
                    }
                }
            }
            
            // Clear references
            objects.clear();
        }
    });
    
    Ok(stats)
}