/*
 * lib.rs - PyO3 Rust bindings for benchlib
 * 
 * This file creates Python bindings using PyO3 for the benchmark C library.
 * Provides equivalent functionality to ctypes/cffi/pybind11 for fair performance comparison.
 */

use pyo3::prelude::*;
use std::os::raw::{c_char, c_int};

// Link to the original C library functions
extern "C" {
    fn noop();
    fn return_int() -> c_int;
    fn return_int64() -> i64;
    fn add_int32(a: i32, b: i32) -> i32;
    fn add_int64(a: i64, b: i64) -> i64;
    fn add_uint64(a: u64, b: u64) -> u64;
    fn logical_and(a: bool, b: bool) -> bool;
    fn logical_or(a: bool, b: bool) -> bool;
    fn logical_not(a: bool) -> bool;
    fn add_float(a: f32, b: f32) -> f32;
    fn add_double(a: f64, b: f64) -> f64;
    fn multiply_double(a: f64, b: f64) -> f64;
    
    // Array operations
    fn sum_doubles_readonly(arr: *const f64, n: usize) -> f64;
    fn scale_doubles_inplace(arr: *mut f64, n: usize, factor: f64);
    fn sum_int32_array(arr: *const i32, n: usize) -> i32;
    fn fill_int32_array(arr: *mut i32, n: usize, value: i32);
    
    // String operations
    fn bytes_length(data: *const c_char, len: usize) -> usize;
    fn utf8_length(str: *const c_char) -> usize;
    fn string_identity(s: *const c_char) -> *const c_char;
    fn string_concat(a: *const c_char, b: *const c_char) -> *mut c_char;
    fn free_string(s: *mut c_char);
    
    // Matrix operations
    fn matrix_multiply_naive(a: *const f64, b: *const f64, c: *mut f64, m: usize, n: usize, k: usize);
    fn dot_product(a: *const f64, b: *const f64, n: usize) -> f64;
    fn vector_add(a: *const f64, b: *const f64, c: *mut f64, n: usize);
    fn vector_norm(v: *const f64, n: usize) -> f64;
    
    // Memory operations
    fn allocate_sized(size: usize) -> *mut i8;
    fn deallocate(ptr: *mut i8);
    
    // Structure operations
    fn create_simple(x: i32, y: i32, value: f64) -> SimpleStructC;
    fn sum_simple(s: *const SimpleStructC) -> f64;
    fn modify_simple(s: *mut SimpleStructC, new_value: f64);
    
    // Callback operations  
    fn c_transform(x: c_int) -> c_int;
    fn apply_callback(x: c_int, transform: extern "C" fn(c_int) -> c_int) -> c_int;
    fn sum_with_transform(arr: *const i32, n: usize, transform: extern "C" fn(i32) -> i32) -> i32;
}

// C struct definition to match benchlib.h
#[repr(C)]
struct SimpleStructC {
    x: i32,
    y: i32, 
    value: f64,
}

// Structure for simple struct operations
#[pyclass]
#[derive(Clone)]
pub struct SimpleStruct {
    #[pyo3(get, set)]
    pub x: i32,
    #[pyo3(get, set)]
    pub y: i32,
    #[pyo3(get, set)]
    pub value: f64,
}

#[pymethods]
impl SimpleStruct {
    #[new]
    fn new() -> Self {
        SimpleStruct { x: 0, y: 0, value: 0.0 }
    }
}

// Basic operations
#[pyfunction]
fn py_noop() {
    unsafe { noop() }
}

#[pyfunction]
fn py_return_int() -> i32 {
    unsafe { return_int() }
}

#[pyfunction]
fn py_return_int64() -> i64 {
    unsafe { return_int64() }
}

// Integer operations
#[pyfunction]
fn py_add_int32(a: i32, b: i32) -> i32 {
    unsafe { add_int32(a, b) }
}

#[pyfunction]
fn py_add_int64(a: i64, b: i64) -> i64 {
    unsafe { add_int64(a, b) }
}

#[pyfunction]
fn py_add_uint64(a: u64, b: u64) -> u64 {
    unsafe { add_uint64(a, b) }
}

// Boolean operations
#[pyfunction]
fn py_logical_and(a: bool, b: bool) -> bool {
    unsafe { logical_and(a, b) }
}

#[pyfunction]
fn py_logical_or(a: bool, b: bool) -> bool {
    unsafe { logical_or(a, b) }
}

#[pyfunction]
fn py_logical_not(a: bool) -> bool {
    unsafe { logical_not(a) }
}

// Floating point operations
#[pyfunction]
fn py_add_float(a: f32, b: f32) -> f32 {
    unsafe { add_float(a, b) }
}

#[pyfunction]
fn py_add_double(a: f64, b: f64) -> f64 {
    unsafe { add_double(a, b) }
}

#[pyfunction]
fn py_multiply_double(a: f64, b: f64) -> f64 {
    unsafe { multiply_double(a, b) }
}

// Array operations - accept Python lists directly (aligned with ctypes)
#[pyfunction]
fn py_sum_doubles_readonly(arr: Vec<f64>) -> f64 {
    unsafe { sum_doubles_readonly(arr.as_ptr(), arr.len()) }
}

#[pyfunction]
fn py_scale_doubles_inplace(mut arr: Vec<f64>, factor: f64) -> Vec<f64> {
    unsafe { scale_doubles_inplace(arr.as_mut_ptr(), arr.len(), factor) };
    arr
}

#[pyfunction]
fn py_sum_int32_array(arr: Vec<i32>) -> i32 {
    unsafe { sum_int32_array(arr.as_ptr(), arr.len()) }
}

#[pyfunction]
fn py_fill_int32_array(mut arr: Vec<i32>, value: i32) -> Vec<i32> {
    unsafe { fill_int32_array(arr.as_mut_ptr(), arr.len(), value) };
    arr
}

// String operations
#[pyfunction]
fn py_bytes_length(data: &[u8], len: usize) -> usize {
    unsafe { bytes_length(data.as_ptr() as *const c_char, len) }
}

#[pyfunction]
fn py_utf8_length(data: &[u8]) -> usize {
    unsafe { utf8_length(data.as_ptr() as *const c_char) }
}

#[pyfunction]
fn py_string_identity(s: &str) -> String {
    let c_str = std::ffi::CString::new(s).unwrap();
    let result_ptr = unsafe { string_identity(c_str.as_ptr()) };
    let result_c_str = unsafe { std::ffi::CStr::from_ptr(result_ptr) };
    result_c_str.to_string_lossy().into_owned()
}

#[pyfunction]
fn py_string_concat(a: &[u8], b: &[u8]) -> String {
    let result_ptr = unsafe { 
        string_concat(
            a.as_ptr() as *const c_char, 
            b.as_ptr() as *const c_char
        )
    };
    if !result_ptr.is_null() {
        let result_c_str = unsafe { std::ffi::CStr::from_ptr(result_ptr) };
        let result = result_c_str.to_string_lossy().into_owned();
        unsafe { free_string(result_ptr) };
        result
    } else {
        String::new()
    }
}

#[pyfunction]  
fn py_free_string(_s: &str) {
    // No-op for PyO3 - memory managed automatically
}

// Structure operations
#[pyfunction]
fn py_create_simple(x: i32, y: i32, value: f64) -> SimpleStruct {
    let c_struct = unsafe { create_simple(x, y, value) };
    SimpleStruct { 
        x: c_struct.x, 
        y: c_struct.y, 
        value: c_struct.value 
    }
}

#[pyfunction]
fn py_sum_simple(s: &SimpleStruct) -> f64 {
    let c_struct = SimpleStructC {
        x: s.x,
        y: s.y, 
        value: s.value,
    };
    unsafe { sum_simple(&c_struct) }
}

#[pyfunction]
fn py_modify_simple(s: &mut SimpleStruct, new_value: f64) {
    let mut c_struct = SimpleStructC {
        x: s.x,
        y: s.y,
        value: s.value,
    };
    unsafe { modify_simple(&mut c_struct, new_value) };
    s.x = c_struct.x;
    s.y = c_struct.y;
    s.value = c_struct.value;
}

// Matrix operations - accept Python lists (aligned with ctypes)
#[pyfunction]
fn py_matrix_multiply_naive(
    a: Vec<f64>,
    b: Vec<f64>,
    mut c: Vec<f64>,
    m: usize,
    n: usize,
    k: usize,
) -> Vec<f64> {
    unsafe {
        matrix_multiply_naive(
            a.as_ptr(),
            b.as_ptr(), 
            c.as_mut_ptr(),
            m,
            n,
            k,
        );
    }
    c
}

#[pyfunction]
fn py_dot_product(a: Vec<f64>, b: Vec<f64>) -> f64 {
    let len = a.len().min(b.len());
    unsafe { dot_product(a.as_ptr(), b.as_ptr(), len) }
}

#[pyfunction]
fn py_vector_add(a: Vec<f64>, b: Vec<f64>, mut c: Vec<f64>) -> Vec<f64> {
    let len = a.len().min(b.len()).min(c.len());
    unsafe {
        vector_add(a.as_ptr(), b.as_ptr(), c.as_mut_ptr(), len);
    }
    c
}

#[pyfunction]
fn py_vector_norm(v: Vec<f64>) -> f64 {
    unsafe { vector_norm(v.as_ptr(), v.len()) }
}

// Memory operations
#[pyfunction]
fn py_allocate_sized(size: usize) -> PyResult<usize> {
    let ptr = unsafe { allocate_sized(size) };
    if ptr.is_null() {
        Ok(0)
    } else {
        Ok(ptr as usize)
    }
}

#[pyfunction]
fn py_deallocate(ptr_addr: usize) {
    if ptr_addr != 0 {
        unsafe { deallocate(ptr_addr as *mut i8) };
    }
}

// Callback operations
#[pyfunction]
fn py_c_transform(x: i32) -> i32 {
    unsafe { c_transform(x) }
}

#[pyfunction]
fn py_apply_callback(x: i32, callback: PyObject) -> PyResult<i32> {
    Python::with_gil(|py| {
        let result = callback.call1(py, (x,))?;
        result.extract(py)
    })
}

#[pyfunction]
fn py_sum_with_transform(arr: Vec<i32>, _size: usize, callback: PyObject) -> PyResult<i32> {
    Python::with_gil(|py| {
        let mut sum = 0;
        for &item in &arr {
            let transformed: i32 = callback.call1(py, (item,))?.extract(py)?;
            sum += transformed;
        }
        Ok(sum)
    })
}

/// A Python module implemented in Rust.
#[pymodule]
fn benchlib_pyo3(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Basic operations
    m.add_function(wrap_pyfunction!(py_noop, m)?)?;
    m.add_function(wrap_pyfunction!(py_return_int, m)?)?;
    m.add_function(wrap_pyfunction!(py_return_int64, m)?)?;
    
    // Integer operations
    m.add_function(wrap_pyfunction!(py_add_int32, m)?)?;
    m.add_function(wrap_pyfunction!(py_add_int64, m)?)?;
    m.add_function(wrap_pyfunction!(py_add_uint64, m)?)?;
    
    // Boolean operations
    m.add_function(wrap_pyfunction!(py_logical_and, m)?)?;
    m.add_function(wrap_pyfunction!(py_logical_or, m)?)?;
    m.add_function(wrap_pyfunction!(py_logical_not, m)?)?;
    
    // Floating point operations
    m.add_function(wrap_pyfunction!(py_add_float, m)?)?;
    m.add_function(wrap_pyfunction!(py_add_double, m)?)?;
    m.add_function(wrap_pyfunction!(py_multiply_double, m)?)?;
    
    // Array operations
    m.add_function(wrap_pyfunction!(py_sum_doubles_readonly, m)?)?;
    m.add_function(wrap_pyfunction!(py_scale_doubles_inplace, m)?)?;
    m.add_function(wrap_pyfunction!(py_sum_int32_array, m)?)?;
    m.add_function(wrap_pyfunction!(py_fill_int32_array, m)?)?;
    
    // String operations
    m.add_function(wrap_pyfunction!(py_bytes_length, m)?)?;
    m.add_function(wrap_pyfunction!(py_utf8_length, m)?)?;
    m.add_function(wrap_pyfunction!(py_string_identity, m)?)?;
    m.add_function(wrap_pyfunction!(py_string_concat, m)?)?;
    m.add_function(wrap_pyfunction!(py_free_string, m)?)?;
    
    // Structure operations
    m.add_class::<SimpleStruct>()?;
    m.add_function(wrap_pyfunction!(py_create_simple, m)?)?;
    m.add_function(wrap_pyfunction!(py_sum_simple, m)?)?;
    m.add_function(wrap_pyfunction!(py_modify_simple, m)?)?;
    
    // Matrix operations
    m.add_function(wrap_pyfunction!(py_matrix_multiply_naive, m)?)?;
    m.add_function(wrap_pyfunction!(py_dot_product, m)?)?;
    m.add_function(wrap_pyfunction!(py_vector_add, m)?)?;
    m.add_function(wrap_pyfunction!(py_vector_norm, m)?)?;
    
    // Memory operations
    m.add_function(wrap_pyfunction!(py_allocate_sized, m)?)?;
    m.add_function(wrap_pyfunction!(py_deallocate, m)?)?;
    
    // Callback operations
    m.add_function(wrap_pyfunction!(py_c_transform, m)?)?;
    m.add_function(wrap_pyfunction!(py_apply_callback, m)?)?;
    m.add_function(wrap_pyfunction!(py_sum_with_transform, m)?)?;
    
    // Add aliases to match the Python function names
    m.add("noop", wrap_pyfunction!(py_noop, m)?)?;
    m.add("return_int", wrap_pyfunction!(py_return_int, m)?)?;
    m.add("return_int64", wrap_pyfunction!(py_return_int64, m)?)?;
    m.add("add_int32", wrap_pyfunction!(py_add_int32, m)?)?;
    m.add("add_int64", wrap_pyfunction!(py_add_int64, m)?)?;
    m.add("add_uint64", wrap_pyfunction!(py_add_uint64, m)?)?;
    m.add("logical_and", wrap_pyfunction!(py_logical_and, m)?)?;
    m.add("logical_or", wrap_pyfunction!(py_logical_or, m)?)?;
    m.add("logical_not", wrap_pyfunction!(py_logical_not, m)?)?;
    m.add("add_float", wrap_pyfunction!(py_add_float, m)?)?;
    m.add("add_double", wrap_pyfunction!(py_add_double, m)?)?;
    m.add("multiply_double", wrap_pyfunction!(py_multiply_double, m)?)?;
    m.add("sum_doubles_readonly", wrap_pyfunction!(py_sum_doubles_readonly, m)?)?;
    m.add("scale_doubles_inplace", wrap_pyfunction!(py_scale_doubles_inplace, m)?)?;
    m.add("sum_int32_array", wrap_pyfunction!(py_sum_int32_array, m)?)?;
    m.add("fill_int32_array", wrap_pyfunction!(py_fill_int32_array, m)?)?;
    m.add("bytes_length", wrap_pyfunction!(py_bytes_length, m)?)?;
    m.add("utf8_length", wrap_pyfunction!(py_utf8_length, m)?)?;
    m.add("string_identity", wrap_pyfunction!(py_string_identity, m)?)?;
    m.add("string_concat", wrap_pyfunction!(py_string_concat, m)?)?;
    m.add("free_string", wrap_pyfunction!(py_free_string, m)?)?;
    m.add("create_simple", wrap_pyfunction!(py_create_simple, m)?)?;
    m.add("sum_simple", wrap_pyfunction!(py_sum_simple, m)?)?;
    m.add("modify_simple", wrap_pyfunction!(py_modify_simple, m)?)?;
    m.add("matrix_multiply_naive", wrap_pyfunction!(py_matrix_multiply_naive, m)?)?;
    m.add("dot_product", wrap_pyfunction!(py_dot_product, m)?)?;
    m.add("vector_add", wrap_pyfunction!(py_vector_add, m)?)?;
    m.add("vector_norm", wrap_pyfunction!(py_vector_norm, m)?)?;
    m.add("allocate_sized", wrap_pyfunction!(py_allocate_sized, m)?)?;
    m.add("deallocate", wrap_pyfunction!(py_deallocate, m)?)?;
    m.add("c_transform", wrap_pyfunction!(py_c_transform, m)?)?;
    m.add("apply_callback", wrap_pyfunction!(py_apply_callback, m)?)?;
    m.add("sum_with_transform", wrap_pyfunction!(py_sum_with_transform, m)?)?;
    
    Ok(())
}