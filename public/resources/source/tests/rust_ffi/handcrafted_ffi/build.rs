// handcrafted_ffi/build.rs
// Build configuration for handcrafted FFI library

fn main() {
    // Link to libc for malloc/free functions
    println!("cargo:rustc-link-lib=c");
    
    // Set specific build optimizations for FFI
    if cfg!(feature = "async_support") {
        println!("cargo:rustc-cfg=feature=\"async_support\"");
    }
    
    // Platform-specific linker flags
    if cfg!(target_os = "macos") {
        // macOS: export all symbols for dylib
        println!("cargo:rustc-cdylib-link-arg=-Wl,-flat_namespace");
    } else if cfg!(target_os = "linux") {
        // Linux: export symbols for dynamic linking
        println!("cargo:rustc-cdylib-link-arg=-Wl,--export-dynamic");
    }
    
    // Add debug information for testing
    if cfg!(debug_assertions) {
        println!("cargo:rustc-link-arg=-g");
    }
}