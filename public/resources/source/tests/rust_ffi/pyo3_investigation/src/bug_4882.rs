// pyo3_investigation/src/bug_4882.rs
// Bug #4882: ABI cache poisoning when toggling GIL vs free-threaded builds

use pyo3::prelude::*;
use std::process::Command;

#[pyfunction]
pub fn test_abi_cache_poisoning() -> PyResult<Vec<String>> {
    let mut issues = Vec::new();
    
    // Test different Python build configurations
    let python_builds = vec![
        ("cpython3.13.5-gil", "Standard GIL build"),
        ("cpython3.13.5-nogil", "Free-threaded build"),
        ("cpython3.14.0rc1-gil", "Python 3.14 GIL build"),
        ("cpython3.14.0rc1-nogil", "Python 3.14 free-threaded build"),
    ];
    
    for (i, (build_name, _description)) in python_builds.iter().enumerate() {
        // Build PyO3 module with specific Python version
        let output = Command::new("cargo")
            .args(&["build", "--release"])
            .env("PYTHON_SYS_EXECUTABLE", format!("./{}/bin/python3", build_name))
            .current_dir(".")
            .output();
            
        match output {
            Ok(result) => {
                if !result.status.success() {
                    let error = String::from_utf8_lossy(&result.stderr);
                    issues.push(format!("Build failed for {}: {}", build_name, error));
                    continue;
                }
                
                // Test cross-loading with other Python builds
                for (j, (test_build, _)) in python_builds.iter().enumerate() {
                    if i == j {
                        continue;  // Skip same build
                    }
                    
                    let import_result = Command::new(format!("./{}/bin/python3", test_build))
                        .args(&["-c", "import pyo3_investigation; print('Import successful')"])
                        .output();
                        
                    match import_result {
                        Ok(import_output) => {
                            if !import_output.status.success() {
                                let error = String::from_utf8_lossy(&import_output.stderr);
                                
                                // Check for ABI poisoning indicators
                                if error.contains("incompatible") || 
                                   error.contains("symbol") ||
                                   error.contains("version") {
                                    issues.push(format!(
                                        "ABI poisoning: Built with {}, failed import with {}: {}",
                                        build_name, test_build, error
                                    ));
                                }
                            }
                        }
                        Err(e) => {
                            issues.push(format!("Failed to test import with {}: {}", test_build, e));
                        }
                    }
                }
            }
            Err(e) => {
                issues.push(format!("Failed to build with {}: {}", build_name, e));
            }
        }
    }
    
    Ok(issues)
}

#[pyfunction]
pub fn demonstrate_build_cache_corruption() -> PyResult<String> {
    // This function demonstrates how build artifacts can become corrupted
    // when switching between GIL and no-GIL builds without proper cleanup
    
    let cache_dirs = vec![
        "target/release",
        "target/debug", 
        ".pyo3-cache",
        "build/lib",
    ];
    
    let mut cache_status = String::new();
    
    for dir in cache_dirs {
        if std::path::Path::new(dir).exists() {
            cache_status.push_str(&format!("Cache directory exists: {}\n", dir));
            
            // Check for potentially problematic files
            if let Ok(entries) = std::fs::read_dir(dir) {
                for entry in entries {
                    if let Ok(entry) = entry {
                        let path = entry.path();
                        if let Some(ext) = path.extension() {
                            if ext == "so" || ext == "pyd" || ext == "dylib" {
                                cache_status.push_str(&format!("  Binary: {:?}\n", path));
                            }
                        }
                    }
                }
            }
        }
    }
    
    Ok(cache_status)
}