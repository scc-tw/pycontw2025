// handcrafted_ffi/src/lib.rs
// Pure manual FFI implementation without PyO3 dependencies

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int, c_void};
use std::ptr;

// Basic test function to verify FFI works
#[no_mangle]
pub extern "C" fn test_function_call() -> c_int {
    42
}

// String conversion test function
#[no_mangle]
pub extern "C" fn test_string_conversion(input: *const c_char) -> *mut c_char {
    if input.is_null() {
        return ptr::null_mut();
    }
    
    unsafe {
        let c_str = CStr::from_ptr(input);
        if let Ok(rust_str) = c_str.to_str() {
            // Process string (reverse it for testing)
            let reversed: String = rust_str.chars().rev().collect();
            
            // Convert back to C string
            if let Ok(c_string) = CString::new(reversed) {
                return c_string.into_raw();
            }
        }
    }
    
    ptr::null_mut()
}

// Memory allocation test functions
#[no_mangle]
pub extern "C" fn test_memory_allocation(size: usize) -> *mut c_void {
    unsafe {
        libc::malloc(size)
    }
}

#[no_mangle]
pub extern "C" fn test_memory_free(ptr: *mut c_void) {
    unsafe {
        if !ptr.is_null() {
            libc::free(ptr);
        }
    }
}

// Concurrent access testing
static mut SHARED_COUNTER: std::sync::atomic::AtomicI32 = std::sync::atomic::AtomicI32::new(0);

#[no_mangle]
pub extern "C" fn create_shared_object() -> *mut c_void {
    // Create a simple object for concurrent testing
    Box::into_raw(Box::new(42)) as *mut c_void
}

#[no_mangle]
pub extern "C" fn concurrent_operation(obj: *mut c_void) -> c_int {
    if obj.is_null() {
        return -1;
    }
    
    unsafe {
        let value = *(obj as *mut i32);
        
        // Simulate some work with atomic operations
        SHARED_COUNTER.fetch_add(value, std::sync::atomic::Ordering::SeqCst)
    }
}

#[no_mangle]
pub extern "C" fn release_shared_object(obj: *mut c_void) {
    if !obj.is_null() {
        unsafe {
            let _boxed = Box::from_raw(obj as *mut i32);
            // Automatic cleanup when Box is dropped
        }
    }
}

// Manual Python object creation without PyO3
#[no_mangle]
pub extern "C" fn manual_create_python_string(input: *const c_char) -> *mut python3_sys::PyObject {
    if input.is_null() {
        return std::ptr::null_mut();
    }
    
    unsafe {
        // Use raw Python C API to create string object
        let py_str = python3_sys::PyUnicode_FromString(input);
        return py_str;
    }
}

// Manual reference counting without PyO3
#[no_mangle]
pub extern "C" fn manual_incref(obj: *mut python3_sys::PyObject) {
    if !obj.is_null() {
        unsafe {
            python3_sys::Py_INCREF(obj);
        }
    }
}

#[no_mangle]
pub extern "C" fn manual_decref(obj: *mut python3_sys::PyObject) {
    if !obj.is_null() {
        unsafe {
            python3_sys::Py_DECREF(obj);
        }
    }
}

// Manual error propagation without PyO3
#[no_mangle]
pub extern "C" fn manual_set_python_exception(exc_type: *const c_char, message: *const c_char) -> c_int {
    if exc_type.is_null() || message.is_null() {
        return -1;
    }
    
    unsafe {
        let c_exc_type = CStr::from_ptr(exc_type);
        let c_message = CStr::from_ptr(message);
        
        if let (Ok(exc_type_str), Ok(message_str)) = (c_exc_type.to_str(), c_message.to_str()) {
            // Use raw Python C API to set exception
            let exc_type_cstr = CString::new(exc_type_str).unwrap();
            let message_cstr = CString::new(message_str).unwrap();
            
            python3_sys::PyErr_SetString(
                python3_sys::PyExc_ValueError, // Simple fallback for now
                message_cstr.as_ptr()
            );
            return 0;
        }
    }
    
    -1
}

// Include modules
pub mod python_types;
pub mod error_handling;

#[cfg(feature = "async_support")]
pub mod async_support;