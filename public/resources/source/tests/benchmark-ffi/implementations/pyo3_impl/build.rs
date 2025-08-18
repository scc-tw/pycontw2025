fn main() {
    // Link to the benchmark library (shared library in ../../lib directory)
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    let benchlib_dir = format!("{}/../../lib", manifest_dir);
    
    println!("cargo:rustc-link-search=native={}", benchlib_dir);
    println!("cargo:rustc-link-lib=benchlib");
    
    // Set RPATH to find benchlib.so at runtime
    #[cfg(target_os = "linux")]
    println!("cargo:rustc-link-arg=-Wl,-rpath,$ORIGIN");
    
    #[cfg(target_os = "macos")]
    println!("cargo:rustc-link-arg=-Wl,-rpath,@loader_path");
    
    // Also tell cargo to rerun if the library changes
    println!("cargo:rerun-if-changed=../../lib/benchlib.c");
    println!("cargo:rerun-if-changed=../../lib/benchlib.so");
}