/*
 * threadtest.cpp - Multi-threaded test library for FFI race condition analysis
 * 
 * This library provides both thread-safe and thread-unsafe functions to
 * demonstrate race conditions in FFI calls from Python.
 * 
 * Compile with -fsanitize=thread for ThreadSanitizer support
 */

#include <atomic>
#include <barrier>
#include <chrono>
#include <condition_variable>
#include <expected>
#include <latch>
#include <mutex>
#include <ranges>
#include <semaphore>
#include <span>
#include <stop_token>
#include <string>
#include <string_view>
#include <thread>
#include <vector>
#include <cstring>
#include <print>
#include <format>
#include <shared_mutex>

// Feature detection for jthread/stop_token
#if defined(__has_include)
#  if !__has_include(<stop_token>)
#    define THREADTEST_NO_JTHREAD 1
#  endif
#endif
#ifndef __cpp_lib_jthread
#  ifndef THREADTEST_NO_JTHREAD
#    define THREADTEST_NO_JTHREAD 1
#  endif
#endif

// Export C interface for Python FFI
extern "C" {

// ============================================================================
// SHARED STATE - Used by both safe and unsafe functions
// ============================================================================

// Global variables for demonstrating race conditions
static long global_counter = 0;  // Intentionally non-atomic for race demos
static long safe_counter = 0;
static std::mutex global_mutex;
static std::shared_mutex shared_mutex;

// Atomic counter for lock-free operations
static std::atomic<long> atomic_counter{0};

// Shared buffer for string operations
static char shared_buffer[1024];
static std::mutex buffer_mutex;

// Modern C++23 features
static std::binary_semaphore data_ready{0};
static std::counting_semaphore<10> resource_pool{10};

// Compiler barrier macro to prevent optimization
#if defined(__GNUC__) || defined(__clang__)
    #define COMPILER_BARRIER() __asm__ __volatile__("" ::: "memory")
#elif defined(_MSC_VER)
    #include <intrin.h>
    #define COMPILER_BARRIER() _ReadWriteBarrier()
#else
    #define COMPILER_BARRIER() std::atomic_thread_fence(std::memory_order_seq_cst)
#endif

// ============================================================================
// INTENTIONALLY BAD CODE - Race conditions for demonstration
// ============================================================================

// BAD: Unsafe increment - has race condition (TSAN will detect this)
long unsafe_increment(int iterations) {
    for (int _ = 0; _ < iterations; _++) {
        // Make race window more visible by adding read-modify-write with barriers
        long temp = global_counter;  // Read
        COMPILER_BARRIER();          // Prevent optimization
        global_counter = temp + 1;   // Write - RACE condition!
        COMPILER_BARRIER();          // Ensure write completes
    }
    return global_counter;
}

// BAD: Unsafe decrement - has race condition
long unsafe_decrement(int iterations) {
    for (int _ = 0; _ < iterations; _++) {
        long temp = global_counter;  // Read
        COMPILER_BARRIER();          // Prevent optimization
        global_counter = temp - 1;   // Write - RACE condition!
        COMPILER_BARRIER();          // Ensure write completes
    }
    return global_counter;
}

// BAD: Read-modify-write race condition
long unsafe_multiply(int factor) {
    long temp = global_counter;  // RACE: Non-atomic read
    std::this_thread::sleep_for(std::chrono::microseconds(1));
    global_counter = temp * factor;  // RACE: Non-atomic write
    return global_counter;
}

// BAD: String buffer race condition
const char* unsafe_write_buffer(const char* text) {
    // NO LOCK - multiple threads will corrupt the buffer
    std::strcpy(shared_buffer, text);  // RACE: Unprotected write
    std::this_thread::sleep_for(std::chrono::microseconds(1));
    std::strcat(shared_buffer, " - processed");  // RACE: Unprotected append
    return shared_buffer;
}

// BAD: Complex operation with multiple race conditions
long unsafe_complex_operation(int value) {
    long result = 0;
    
    // Multiple non-atomic operations creating races
    global_counter += value;     // RACE
    result = global_counter;      // RACE
    global_counter *= 2;          // RACE
    result += global_counter;     // RACE
    global_counter -= value;      // RACE
    
    return result;
}

// BAD: Double-checked locking anti-pattern (broken!)
static void* singleton = nullptr;
static std::mutex singleton_mutex;

void* get_singleton_unsafe() {
    if (singleton == nullptr) {  // RACE: Non-atomic read
        std::lock_guard lock(singleton_mutex);
        if (singleton == nullptr) {
            singleton = std::malloc(100);  // RACE: Non-atomic write visible outside mutex
        }
    }
    return singleton;
}

// BAD: TOCTOU (Time-of-check to time-of-use) race
static long bank_balance = 1000;  // Intentionally non-atomic

int withdraw_unsafe(long amount) {
    if (bank_balance >= amount) {  // CHECK: Read balance
        // Increase delay to make race condition more likely
        // This simulates real-world processing delay between check and use
        std::this_thread::sleep_for(std::chrono::microseconds(100));
        
        // Add another check to show the problem more clearly
        long temp = bank_balance;  // Read current balance
        std::this_thread::sleep_for(std::chrono::microseconds(50));
        bank_balance = temp - amount;  // USE: Balance might have changed! RACE!
        return 1;
    }
    return 0;
}

// BAD: Fast TOCTOU without sleep (for GIL vs no-GIL comparison)
static long fast_bank_balance = 1000;  // Intentionally non-atomic

int withdraw_unsafe_fast(long amount) {
    if (fast_bank_balance >= amount) {  // CHECK: Read balance
        // No sleep - just compiler barriers to create a race window
        long temp = fast_bank_balance;
        COMPILER_BARRIER();  // Prevent compiler from optimizing out the read
        
        // Do some minimal work to create race window without releasing GIL
        for (int _ = 0; _ < 100; _++) {
            COMPILER_BARRIER();  // Ensure loop isn't optimized away
        }
        
        COMPILER_BARRIER();  // Ensure write happens after loop
        fast_bank_balance = temp - amount;  // USE: Balance might have changed! RACE!
        return 1;
    }
    return 0;
}

long get_fast_bank_balance() {
    return fast_bank_balance;
}

void reset_fast_bank() {
    fast_bank_balance = 1000;
}

// ============================================================================
// GOOD CODE - Thread-safe implementations using modern C++23
// ============================================================================

// GOOD: Safe increment using scoped_lock (C++17)
long safe_increment(int iterations) {
    std::scoped_lock lock(global_mutex);
    for (int _ = 0; _ < iterations; _++) {
        safe_counter++;
    }
    return safe_counter;
}

// GOOD: Safe decrement using lock_guard
long safe_decrement(int iterations) {
    std::lock_guard lock(global_mutex);  // CTAD since C++17
    for (int _ = 0; _ < iterations; _++) {
        safe_counter--;
    }
    return safe_counter;
}

// GOOD: Safe multiply using unique_lock
long safe_multiply(int factor) {
    std::unique_lock lock(global_mutex);
    safe_counter *= factor;
    return safe_counter;
}

// GOOD: Safe buffer write with proper locking
const char* safe_write_buffer(const char* text) {
    std::lock_guard lock(buffer_mutex);
    std::strcpy(shared_buffer, text);
    std::strcat(shared_buffer, " - processed");
    return shared_buffer;
}

// GOOD: Complex operation with proper synchronization
long safe_complex_operation(int value) {
    std::scoped_lock lock(global_mutex);
    
    safe_counter += value;
    long result = safe_counter;
    safe_counter *= 2;
    result += safe_counter;
    safe_counter -= value;
    
    return result;
}

// GOOD: Proper singleton with std::once_flag (C++11)
static std::once_flag singleton_flag;
static std::atomic<void*> safe_singleton{nullptr};

void* get_singleton_safe() {
    std::call_once(singleton_flag, []() {
        void* ptr = std::malloc(100);
        safe_singleton.store(ptr, std::memory_order_release);
    });
    return safe_singleton.load(std::memory_order_acquire);
}

// GOOD: Atomic bank operations
static std::atomic<long> atomic_bank_balance{1000};

int withdraw_safe(long amount) {
    long current = atomic_bank_balance.load();
    while (current >= amount) {
        if (atomic_bank_balance.compare_exchange_weak(current, current - amount)) {
            return 1;  // Success
        }
        // current is updated by compare_exchange_weak if it fails
    }
    return 0;  // Insufficient funds
}

// ============================================================================
// MODERN C++23 PATTERNS
// ============================================================================

// Using std::atomic_ref (C++20) for existing non-atomic data
long modern_atomic_ref_increment(long& target, int iterations) {
    std::atomic_ref<long> atomic_target(target);
    for (int i = 0; i < iterations; i++) {
        atomic_target.fetch_add(1, std::memory_order_relaxed);
    }
    return atomic_target.load();
}

#ifndef THREADTEST_NO_JTHREAD
// Using std::jthread (C++20) with stop_token
static std::atomic<long> jthread_counter{0};

void jthread_worker(std::stop_token stoken) {
    while (!stoken.stop_requested()) {
        jthread_counter.fetch_add(1, std::memory_order_relaxed);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

long start_jthread_worker() {
    static std::jthread worker;
    
    if (!worker.joinable()) {
        worker = std::jthread(jthread_worker);
    }
    
    return jthread_counter.load();
}

void stop_jthread_worker() {
    static std::jthread worker;
    if (worker.joinable()) {
        worker.request_stop();
        worker.join();
    }
}
#else
// Fallback implementation when jthread/stop_token are unavailable
static std::atomic<long> jthread_counter{0};
static std::atomic<bool> jthread_stop_flag{false};
static std::thread jthread_fallback_worker;

static void jthread_worker_fallback() {
    while (!jthread_stop_flag.load(std::memory_order_relaxed)) {
        jthread_counter.fetch_add(1, std::memory_order_relaxed);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

long start_jthread_worker() {
    if (!jthread_fallback_worker.joinable()) {
        jthread_stop_flag.store(false, std::memory_order_relaxed);
        jthread_fallback_worker = std::thread(jthread_worker_fallback);
    }
    return jthread_counter.load();
}

void stop_jthread_worker() {
    if (jthread_fallback_worker.joinable()) {
        jthread_stop_flag.store(true, std::memory_order_relaxed);
        jthread_fallback_worker.join();
    }
}
#endif

// Using std::barrier (C++20) for synchronization
static std::barrier sync_barrier{4};  // For 4 threads

void barrier_increment() {
    global_counter++;  // Intentionally unsafe
    sync_barrier.arrive_and_wait();
    // All threads have incremented before any continue
}

// Using std::latch (C++20) for one-time synchronization
static std::latch start_latch{1};

void latch_wait_and_increment() {
    start_latch.wait();  // Wait for signal
    global_counter++;    // Race condition after latch
}

void latch_signal() {
    start_latch.count_down();  // Release all waiting threads
}

// ============================================================================
// ATOMIC OPERATIONS - Lock-free implementations
// ============================================================================

// Atomic increment with different memory orderings
long atomic_increment(int iterations) {
    for (int i = 0; i < iterations; i++) {
        atomic_counter.fetch_add(1, std::memory_order_relaxed);
    }
    return atomic_counter.load(std::memory_order_acquire);
}

// Atomic decrement
long atomic_decrement(int iterations) {
    for (int i = 0; i < iterations; i++) {
        atomic_counter.fetch_sub(1, std::memory_order_relaxed);
    }
    return atomic_counter.load(std::memory_order_acquire);
}

// Compare and swap
int atomic_cas(long expected, long desired) {
    return atomic_counter.compare_exchange_strong(
        expected, desired,
        std::memory_order_acq_rel,
        std::memory_order_acquire
    );
}

// Atomic wait/notify (C++20)
void atomic_wait_for_value(long value) {
    atomic_counter.wait(value);  // Block until counter != value
}

void atomic_notify_one() {
    atomic_counter.notify_one();
}

void atomic_notify_all() {
    atomic_counter.notify_all();
}

// ============================================================================
// READER-WRITER PATTERNS
// ============================================================================

// BAD: Unprotected reader-writer
static long shared_data = 0;

long unsafe_read() {
    return shared_data;  // RACE: Concurrent write possible
}

void unsafe_write(long value) {
    shared_data = value;  // RACE: Concurrent read/write possible
}

// GOOD: Protected with shared_mutex (C++17)
long safe_read() {
    std::shared_lock lock(shared_mutex);  // Multiple readers allowed
    return safe_counter;
}

void safe_write(long value) {
    std::unique_lock lock(shared_mutex);  // Exclusive write access
    safe_counter = value;
}

// ============================================================================
// DEADLOCK SCENARIOS
// ============================================================================

static std::mutex lock1, lock2;

// BAD: Can deadlock with opposite lock ordering
void deadlock_function1() {
    std::lock_guard l1(lock1);
    std::this_thread::sleep_for(std::chrono::microseconds(100));
    std::lock_guard l2(lock2);  // DEADLOCK: If function2 has lock2
    global_counter++;
}

void deadlock_function2() {
    std::lock_guard l2(lock2);  // Opposite order!
    std::this_thread::sleep_for(std::chrono::microseconds(100));
    std::lock_guard l1(lock1);  // DEADLOCK: If function1 has lock1
    global_counter++;
}

// GOOD: Using std::scoped_lock to avoid deadlock (C++17)
int safe_dual_lock_operation() {
    std::scoped_lock lock(lock1, lock2);  // Acquires both atomically
    global_counter++;
    return global_counter;
}

// ============================================================================
// RESET AND UTILITY FUNCTIONS
// ============================================================================

void reset_counters() {
    std::scoped_lock lock(global_mutex, buffer_mutex, shared_mutex);
    
    global_counter = 0;
    safe_counter = 0;
    atomic_counter.store(0);
    std::memset(shared_buffer, 0, sizeof(shared_buffer));
    atomic_bank_balance.store(1000);
    bank_balance = 1000;
    fast_bank_balance = 1000;
    shared_data = 0;
    jthread_counter.store(0);
}

long get_global_counter() {
    return global_counter;  // Intentionally unsafe for testing
}

long get_safe_counter() {
    std::lock_guard lock(global_mutex);
    return safe_counter;
}

long get_atomic_counter() {
    return atomic_counter.load(std::memory_order_acquire);
}

long get_balance() {
    return atomic_bank_balance.load();
}

long get_unsafe_balance() {
    return bank_balance;  // Intentionally unsafe
}

// ============================================================================
// SEMAPHORE EXAMPLES (C++20)
// ============================================================================

int acquire_resource() {
    if (resource_pool.try_acquire()) {
        return 1;  // Got resource
    }
    return 0;  // No resources available
}

int acquire_resource_timeout(int ms) {
    if (resource_pool.try_acquire_for(std::chrono::milliseconds(ms))) {
        return 1;
    }
    return 0;
}

void release_resource() {
    resource_pool.release();
}

void signal_data_ready() {
    data_ready.release();
}

void wait_for_data() {
    data_ready.acquire();
}

} // extern "C"