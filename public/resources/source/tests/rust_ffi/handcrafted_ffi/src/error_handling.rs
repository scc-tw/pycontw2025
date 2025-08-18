// handcrafted_ffi/src/error_handling.rs
// Custom error propagation across FFI boundary

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int};
use std::fmt;

#[repr(C)]
pub struct RustError {
    pub error_code: c_int,
    pub message: *mut c_char,
    pub rust_backtrace: *mut c_char,
}

#[derive(Debug)]
pub enum FFIError {
    NullPointer,
    InvalidUtf8,
    PythonException(String),
    MemoryAllocation,
    RustPanic(String),
}

impl fmt::Display for FFIError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            FFIError::NullPointer => write!(f, "Null pointer passed to FFI"),
            FFIError::InvalidUtf8 => write!(f, "Invalid UTF-8 sequence"),
            FFIError::PythonException(msg) => write!(f, "Python exception: {}", msg),
            FFIError::MemoryAllocation => write!(f, "Memory allocation failed"),
            FFIError::RustPanic(msg) => write!(f, "Rust panic: {}", msg),
        }
    }
}

pub struct ErrorContext {
    last_error: Option<FFIError>,
    error_callback: Option<extern "C" fn(*const RustError)>,
}

static mut ERROR_CONTEXT: ErrorContext = ErrorContext {
    last_error: None,
    error_callback: None,
};

impl ErrorContext {
    pub fn set_error(&mut self, error: FFIError) {
        if let Some(callback) = self.error_callback {
            let rust_error = self.convert_to_c_error(&error);
            callback(&rust_error);
        }
        self.last_error = Some(error);
    }
    
    fn convert_to_c_error(&self, error: &FFIError) -> RustError {
        let message = CString::new(error.to_string()).unwrap_or_default();
        let backtrace = CString::new("Backtrace not available in this simplified implementation")
            .unwrap_or_default();
            
        RustError {
            error_code: match error {
                FFIError::NullPointer => 1,
                FFIError::InvalidUtf8 => 2,
                FFIError::PythonException(_) => 3,
                FFIError::MemoryAllocation => 4,
                FFIError::RustPanic(_) => 5,
            },
            message: message.into_raw(),
            rust_backtrace: backtrace.into_raw(),
        }
    }
}

// Error handling functions
#[no_mangle]
pub extern "C" fn set_error_callback(callback: extern "C" fn(*const RustError)) {
    unsafe {
        ERROR_CONTEXT.error_callback = Some(callback);
    }
}

#[no_mangle]
pub extern "C" fn get_last_error() -> *const RustError {
    unsafe {
        if let Some(ref error) = ERROR_CONTEXT.last_error {
            let rust_error = ERROR_CONTEXT.convert_to_c_error(error);
            Box::into_raw(Box::new(rust_error))
        } else {
            std::ptr::null()
        }
    }
}

#[no_mangle]
pub extern "C" fn clear_last_error() {
    unsafe {
        ERROR_CONTEXT.last_error = None;
    }
}

// Safe function wrapper with error handling
pub fn safe_ffi_call<F, R>(func: F) -> R
where
    F: FnOnce() -> Result<R, FFIError> + std::panic::UnwindSafe,
    R: Default,
{
    match std::panic::catch_unwind(func) {
        Ok(Ok(result)) => result,
        Ok(Err(error)) => {
            unsafe {
                ERROR_CONTEXT.set_error(error);
            }
            R::default()
        }
        Err(panic) => {
            let panic_msg = if let Some(s) = panic.downcast_ref::<&'static str>() {
                s.to_string()
            } else if let Some(s) = panic.downcast_ref::<String>() {
                s.clone()
            } else {
                "Unknown panic".to_string()
            };
            
            unsafe {
                ERROR_CONTEXT.set_error(FFIError::RustPanic(panic_msg));
            }
            R::default()
        }
    }
}

// Helper wrapper for pointer return types
fn safe_ffi_call_ptr<F>(func: F) -> *mut c_char
where
    F: FnOnce() -> Result<*mut c_char, FFIError> + std::panic::UnwindSafe,
{
    match std::panic::catch_unwind(func) {
        Ok(Ok(result)) => result,
        Ok(Err(error)) => {
            unsafe {
                ERROR_CONTEXT.set_error(error);
            }
            std::ptr::null_mut()
        }
        Err(panic) => {
            let panic_msg = if let Some(s) = panic.downcast_ref::<&'static str>() {
                s.to_string()
            } else if let Some(s) = panic.downcast_ref::<String>() {
                s.clone()
            } else {
                "Unknown panic".to_string()
            };
            
            unsafe {
                ERROR_CONTEXT.set_error(FFIError::RustPanic(panic_msg));
            }
            std::ptr::null_mut()
        }
    }
}

// Example usage with error handling
#[no_mangle]
pub extern "C" fn safe_string_operation(input: *const c_char) -> *mut c_char {
    safe_ffi_call_ptr(|| {
        if input.is_null() {
            return Err(FFIError::NullPointer);
        }
        
        unsafe {
            let c_str = CStr::from_ptr(input);
            let rust_str = c_str.to_str().map_err(|_| FFIError::InvalidUtf8)?;
            
            let result = format!("Processed: {}", rust_str);
            let c_result = CString::new(result).map_err(|_| FFIError::InvalidUtf8)?;
            
            Ok(c_result.into_raw())
        }
    })
}