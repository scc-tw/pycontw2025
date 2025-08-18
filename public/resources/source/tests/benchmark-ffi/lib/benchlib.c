/*
 * benchlib.c - Shared C library for FFI benchmark testing
 * 
 * This library provides identical C entry points for all FFI methods
 * to ensure fair performance comparison.
 */

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <math.h>

#ifdef __GLIBC__
#include <malloc.h>
#endif

// Forward declarations
int return_int(void);

// Export macros for shared library
#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif

// =============================================================================
// 1. Baseline Measurements
// =============================================================================

// Null baseline - pure C function call
EXPORT void null_baseline() { }

// C→C baseline for direct comparison
EXPORT int c_to_c_baseline(int iterations) {
    int result = 0;
    for (int i = 0; i < iterations; i++) {
        result += return_int();  // Direct C function call
    }
    return result;
}

// Minimal FFI overhead test
EXPORT void noop() { }
EXPORT int return_int() { return 42; }
EXPORT int64_t return_int64() { return 0x123456789ABCDEF0LL; }
EXPORT bool return_bool() { return true; }
EXPORT double return_double() { return 3.14159265358979; }

// =============================================================================
// 1A. Dispatch Pattern Test Functions (100+ functions)
// =============================================================================

// Auto-generated dispatch test functions for pattern benchmarking
#define DECLARE_DISPATCH_FUNC(n) \
    EXPORT int dispatch_test_##n(int a, int b) { return a + b + n; }

// Generate 100 dispatch test functions
DECLARE_DISPATCH_FUNC(0)   DECLARE_DISPATCH_FUNC(1)   DECLARE_DISPATCH_FUNC(2)   DECLARE_DISPATCH_FUNC(3)   DECLARE_DISPATCH_FUNC(4)
DECLARE_DISPATCH_FUNC(5)   DECLARE_DISPATCH_FUNC(6)   DECLARE_DISPATCH_FUNC(7)   DECLARE_DISPATCH_FUNC(8)   DECLARE_DISPATCH_FUNC(9)
DECLARE_DISPATCH_FUNC(10)  DECLARE_DISPATCH_FUNC(11)  DECLARE_DISPATCH_FUNC(12)  DECLARE_DISPATCH_FUNC(13)  DECLARE_DISPATCH_FUNC(14)
DECLARE_DISPATCH_FUNC(15)  DECLARE_DISPATCH_FUNC(16)  DECLARE_DISPATCH_FUNC(17)  DECLARE_DISPATCH_FUNC(18)  DECLARE_DISPATCH_FUNC(19)
DECLARE_DISPATCH_FUNC(20)  DECLARE_DISPATCH_FUNC(21)  DECLARE_DISPATCH_FUNC(22)  DECLARE_DISPATCH_FUNC(23)  DECLARE_DISPATCH_FUNC(24)
DECLARE_DISPATCH_FUNC(25)  DECLARE_DISPATCH_FUNC(26)  DECLARE_DISPATCH_FUNC(27)  DECLARE_DISPATCH_FUNC(28)  DECLARE_DISPATCH_FUNC(29)
DECLARE_DISPATCH_FUNC(30)  DECLARE_DISPATCH_FUNC(31)  DECLARE_DISPATCH_FUNC(32)  DECLARE_DISPATCH_FUNC(33)  DECLARE_DISPATCH_FUNC(34)
DECLARE_DISPATCH_FUNC(35)  DECLARE_DISPATCH_FUNC(36)  DECLARE_DISPATCH_FUNC(37)  DECLARE_DISPATCH_FUNC(38)  DECLARE_DISPATCH_FUNC(39)
DECLARE_DISPATCH_FUNC(40)  DECLARE_DISPATCH_FUNC(41)  DECLARE_DISPATCH_FUNC(42)  DECLARE_DISPATCH_FUNC(43)  DECLARE_DISPATCH_FUNC(44)
DECLARE_DISPATCH_FUNC(45)  DECLARE_DISPATCH_FUNC(46)  DECLARE_DISPATCH_FUNC(47)  DECLARE_DISPATCH_FUNC(48)  DECLARE_DISPATCH_FUNC(49)
DECLARE_DISPATCH_FUNC(50)  DECLARE_DISPATCH_FUNC(51)  DECLARE_DISPATCH_FUNC(52)  DECLARE_DISPATCH_FUNC(53)  DECLARE_DISPATCH_FUNC(54)
DECLARE_DISPATCH_FUNC(55)  DECLARE_DISPATCH_FUNC(56)  DECLARE_DISPATCH_FUNC(57)  DECLARE_DISPATCH_FUNC(58)  DECLARE_DISPATCH_FUNC(59)
DECLARE_DISPATCH_FUNC(60)  DECLARE_DISPATCH_FUNC(61)  DECLARE_DISPATCH_FUNC(62)  DECLARE_DISPATCH_FUNC(63)  DECLARE_DISPATCH_FUNC(64)
DECLARE_DISPATCH_FUNC(65)  DECLARE_DISPATCH_FUNC(66)  DECLARE_DISPATCH_FUNC(67)  DECLARE_DISPATCH_FUNC(68)  DECLARE_DISPATCH_FUNC(69)
DECLARE_DISPATCH_FUNC(70)  DECLARE_DISPATCH_FUNC(71)  DECLARE_DISPATCH_FUNC(72)  DECLARE_DISPATCH_FUNC(73)  DECLARE_DISPATCH_FUNC(74)
DECLARE_DISPATCH_FUNC(75)  DECLARE_DISPATCH_FUNC(76)  DECLARE_DISPATCH_FUNC(77)  DECLARE_DISPATCH_FUNC(78)  DECLARE_DISPATCH_FUNC(79)
DECLARE_DISPATCH_FUNC(80)  DECLARE_DISPATCH_FUNC(81)  DECLARE_DISPATCH_FUNC(82)  DECLARE_DISPATCH_FUNC(83)  DECLARE_DISPATCH_FUNC(84)
DECLARE_DISPATCH_FUNC(85)  DECLARE_DISPATCH_FUNC(86)  DECLARE_DISPATCH_FUNC(87)  DECLARE_DISPATCH_FUNC(88)  DECLARE_DISPATCH_FUNC(89)
DECLARE_DISPATCH_FUNC(90)  DECLARE_DISPATCH_FUNC(91)  DECLARE_DISPATCH_FUNC(92)  DECLARE_DISPATCH_FUNC(93)  DECLARE_DISPATCH_FUNC(94)
DECLARE_DISPATCH_FUNC(95)  DECLARE_DISPATCH_FUNC(96)  DECLARE_DISPATCH_FUNC(97)  DECLARE_DISPATCH_FUNC(98)  DECLARE_DISPATCH_FUNC(99)

// C-side dispatch function table for baseline comparison
typedef int (*dispatch_func_t)(int, int);

static dispatch_func_t dispatch_function_table[100] = {
    dispatch_test_0,  dispatch_test_1,  dispatch_test_2,  dispatch_test_3,  dispatch_test_4,
    dispatch_test_5,  dispatch_test_6,  dispatch_test_7,  dispatch_test_8,  dispatch_test_9,
    dispatch_test_10, dispatch_test_11, dispatch_test_12, dispatch_test_13, dispatch_test_14,
    dispatch_test_15, dispatch_test_16, dispatch_test_17, dispatch_test_18, dispatch_test_19,
    dispatch_test_20, dispatch_test_21, dispatch_test_22, dispatch_test_23, dispatch_test_24,
    dispatch_test_25, dispatch_test_26, dispatch_test_27, dispatch_test_28, dispatch_test_29,
    dispatch_test_30, dispatch_test_31, dispatch_test_32, dispatch_test_33, dispatch_test_34,
    dispatch_test_35, dispatch_test_36, dispatch_test_37, dispatch_test_38, dispatch_test_39,
    dispatch_test_40, dispatch_test_41, dispatch_test_42, dispatch_test_43, dispatch_test_44,
    dispatch_test_45, dispatch_test_46, dispatch_test_47, dispatch_test_48, dispatch_test_49,
    dispatch_test_50, dispatch_test_51, dispatch_test_52, dispatch_test_53, dispatch_test_54,
    dispatch_test_55, dispatch_test_56, dispatch_test_57, dispatch_test_58, dispatch_test_59,
    dispatch_test_60, dispatch_test_61, dispatch_test_62, dispatch_test_63, dispatch_test_64,
    dispatch_test_65, dispatch_test_66, dispatch_test_67, dispatch_test_68, dispatch_test_69,
    dispatch_test_70, dispatch_test_71, dispatch_test_72, dispatch_test_73, dispatch_test_74,
    dispatch_test_75, dispatch_test_76, dispatch_test_77, dispatch_test_78, dispatch_test_79,
    dispatch_test_80, dispatch_test_81, dispatch_test_82, dispatch_test_83, dispatch_test_84,
    dispatch_test_85, dispatch_test_86, dispatch_test_87, dispatch_test_88, dispatch_test_89,
    dispatch_test_90, dispatch_test_91, dispatch_test_92, dispatch_test_93, dispatch_test_94,
    dispatch_test_95, dispatch_test_96, dispatch_test_97, dispatch_test_98, dispatch_test_99
};

// C-side dispatch for baseline comparison
EXPORT int dispatch_c_baseline(int func_id, int a, int b) {
    if (func_id >= 0 && func_id < 100) {
        return dispatch_function_table[func_id](a, b);
    }
    return -1;
}

// =============================================================================
// 2. Type Conversion Tests
// =============================================================================

// Integer type matrix
EXPORT int32_t add_int32(int32_t a, int32_t b) { return a + b; }
EXPORT int64_t add_int64(int64_t a, int64_t b) { return a + b; }
EXPORT uint64_t add_uint64(uint64_t a, uint64_t b) { return a + b; }

// Overflow boundary tests
EXPORT int64_t handle_overflow(int64_t a, int64_t b) {
    // Test Python bigint conversion paths
    return a * b;
}

// Boolean handling
EXPORT bool logical_and(bool a, bool b) { return a && b; }
EXPORT bool logical_or(bool a, bool b) { return a || b; }
EXPORT bool logical_not(bool a) { return !a; }

// Float/double operations
EXPORT float add_float(float a, float b) { return a + b; }
EXPORT double add_double(double a, double b) { return a + b; }
EXPORT double multiply_double(double a, double b) { return a * b; }

// =============================================================================
// 3. String Operations
// =============================================================================

// Split bytes vs str handling
EXPORT size_t bytes_length(const char* data, size_t len) {
    // Process as raw bytes, no encoding assumptions
    (void)data;  // Silence unused parameter warning
    return len;
}

EXPORT size_t utf8_length(const char* str) {
    // Validate UTF-8 and count characters
    size_t chars = 0;
    while (*str) {
        if ((*str & 0xC0) != 0x80) chars++;
        str++;
    }
    return chars;
}

// Test borrowed vs owned memory
EXPORT const char* string_identity(const char* s) {
    return s;  // Borrowed - caller owns
}

EXPORT char* string_concat(const char* a, const char* b) {
    size_t len_a = strlen(a);
    size_t len_b = strlen(b);
    char* result = (char*)malloc(len_a + len_b + 1);
    if (!result) return NULL;
    strcpy(result, a);
    strcat(result, b);
    return result;  // Caller must free
}

EXPORT void free_string(char* s) {
    free(s);  // Matching free for consistency
}

// Edge cases
EXPORT bool has_null_byte(const char* data, size_t len) {
    return memchr(data, 0, len) != NULL;
}

EXPORT size_t count_bytes(const uint8_t* data, size_t len, uint8_t target) {
    size_t count = 0;
    for (size_t i = 0; i < len; i++) {
        if (data[i] == target) count++;
    }
    return count;
}

// =============================================================================
// 4. Array/Buffer Operations
// =============================================================================

// Zero-copy capable operations
EXPORT double sum_doubles_readonly(const double* arr, size_t n) {
    double sum = 0.0;
    for (size_t i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum;
}

EXPORT void scale_doubles_inplace(double* arr, size_t n, double factor) {
    for (size_t i = 0; i < n; i++) {
        arr[i] *= factor;
    }
}

// Test alignment and stride handling
EXPORT double sum_strided(const double* arr, size_t n, ptrdiff_t stride) {
    double sum = 0.0;
    const char* ptr = (const char*)arr;
    for (size_t i = 0; i < n; i++) {
        sum += *(const double*)(ptr + i * stride);
    }
    return sum;
}

// Verify buffer requirements
EXPORT bool is_aligned(const void* ptr, size_t alignment) {
    return ((uintptr_t)ptr % alignment) == 0;
}

// Integer array operations
EXPORT int32_t sum_int32_array(const int32_t* arr, size_t n) {
    int32_t sum = 0;
    for (size_t i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum;
}

EXPORT void fill_int32_array(int32_t* arr, size_t n, int32_t value) {
    for (size_t i = 0; i < n; i++) {
        arr[i] = value;
    }
}

// =============================================================================
// 5. Structure Operations
// =============================================================================

// Simple struct with known layout
typedef struct {
    int32_t x;
    int32_t y;
    double value;
} SimpleStruct;

// Verify size and alignment at compile time
_Static_assert(sizeof(SimpleStruct) == 16, "SimpleStruct size mismatch");
_Static_assert(offsetof(SimpleStruct, value) == 8, "SimpleStruct layout mismatch");

EXPORT SimpleStruct create_simple(int32_t x, int32_t y, double value) {
    return (SimpleStruct){x, y, value};
}

EXPORT double sum_simple(const SimpleStruct* s) {
    return s->x + s->y + s->value;
}

EXPORT void modify_simple(SimpleStruct* s, double new_value) {
    s->value = new_value;
}

// Complex nested struct
typedef struct {
    SimpleStruct points[4];
    char name[32];
    struct {
        size_t count;
        double* data;  // Owned pointer
    } buffer;
} ComplexStruct;

_Static_assert(sizeof(ComplexStruct) == 112, "ComplexStruct size mismatch");

EXPORT ComplexStruct* create_complex(const char* name, size_t count) {
    ComplexStruct* s = (ComplexStruct*)calloc(1, sizeof(ComplexStruct));
    if (!s) return NULL;
    
    strncpy(s->name, name, 31);
    s->name[31] = '\0';  // Ensure null termination
    s->buffer.count = count;
    
    if (count > 0) {
        s->buffer.data = (double*)calloc(count, sizeof(double));
        if (!s->buffer.data) {
            free(s);
            return NULL;
        }
    }
    
    return s;
}

EXPORT void free_complex(ComplexStruct* s) {
    if (s) {
        free(s->buffer.data);
        free(s);
    }
}

EXPORT double sum_complex_buffer(const ComplexStruct* s) {
    if (!s || !s->buffer.data) return 0.0;
    
    double sum = 0.0;
    for (size_t i = 0; i < s->buffer.count; i++) {
        sum += s->buffer.data[i];
    }
    return sum;
}

// =============================================================================
// 6. Callback Tests
// =============================================================================

// Simple callback
EXPORT int32_t apply_callback(int32_t x, int32_t (*transform)(int32_t)) {
    return transform(x);
}

// Callback with error handling
typedef enum { SUCCESS = 0, ERROR = -1 } status_t;

EXPORT status_t iterate_with_callback(
    const double* data, 
    size_t n,
    status_t (*process)(size_t index, double value, void* context),
    void* context
) {
    for (size_t i = 0; i < n; i++) {
        status_t result = process(i, data[i], context);
        if (result != SUCCESS) {
            return result;
        }
    }
    return SUCCESS;
}

// C-to-C baseline callback
EXPORT int32_t c_transform(int32_t x) { return x * 2; }

// Test callback performance
EXPORT int32_t sum_with_transform(const int32_t* arr, size_t n, 
                                 int32_t (*transform)(int32_t)) {
    int32_t sum = 0;
    for (size_t i = 0; i < n; i++) {
        sum += transform(arr[i]);
    }
    return sum;
}

// =============================================================================
// 7. Memory Allocation Patterns
// =============================================================================

// Allocation size matrix
EXPORT void* allocate_sized(size_t size) {
    return malloc(size);
}

EXPORT void* allocate_aligned(size_t size, size_t alignment) {
    void* ptr = NULL;
    #ifdef _WIN32
        ptr = _aligned_malloc(size, alignment);
    #else
        if (posix_memalign(&ptr, alignment, size) != 0) {
            return NULL;
        }
    #endif
    return ptr;
}

EXPORT void deallocate(void* ptr) {
    free(ptr);
}

EXPORT void deallocate_aligned(void* ptr) {
    #ifdef _WIN32
        _aligned_free(ptr);
    #else
        free(ptr);
    #endif
}

// Arena leak trigger pattern (for glibc arena leak PoC)
EXPORT void* trigger_arena_pattern(size_t iterations) {
    // Allocate in pattern known to fragment arenas
    for (size_t i = 0; i < iterations; i++) {
        size_t size = 1024 + (i % 1024);
        void* ptr = malloc(size);
        if (i % 2 == 0) {
            free(ptr);
        }
        // Leak every other allocation
    }
    return NULL;
}

// Memory statistics (glibc-specific)
typedef struct {
    size_t heap_size;
    size_t n_arenas;
    size_t arena_bytes;
    size_t used_bytes;
    size_t free_bytes;
} mem_stats_t;

#ifdef __GLIBC__
EXPORT void get_malloc_stats(mem_stats_t* stats) {
    struct mallinfo2 mi = mallinfo2();
    stats->heap_size = mi.hblkhd + mi.uordblks;
    stats->used_bytes = mi.uordblks;
    stats->free_bytes = mi.fordblks;
    // Note: narenas field doesn't exist in mallinfo2
    // Would need malloc_stats() for detailed arena info
    stats->n_arenas = 0;  // Placeholder
    stats->arena_bytes = mi.hblkhd;
}

EXPORT int do_malloc_trim(size_t pad) {
    return malloc_trim(pad);
}
#else
EXPORT void get_malloc_stats(mem_stats_t* stats) {
    // Non-glibc placeholder
    memset(stats, 0, sizeof(mem_stats_t));
}

EXPORT int do_malloc_trim(size_t pad) {
    (void)pad;
    return 0;  // Not supported
}
#endif

// =============================================================================
// 8. Compute Workload (Crossover Point Analysis)
// =============================================================================

// Dense computation to find overhead amortization point
EXPORT void matrix_multiply_naive(
    const double* a, const double* b, double* c,
    size_t m, size_t n, size_t k
) {
    for (size_t i = 0; i < m; i++) {
        for (size_t j = 0; j < n; j++) {
            double sum = 0.0;
            for (size_t l = 0; l < k; l++) {
                sum += a[i * k + l] * b[l * n + j];
            }
            c[i * n + j] = sum;
        }
    }
}

// Varying workload sizes to find crossover
EXPORT double dot_product(const double* a, const double* b, size_t n) {
    double sum = 0.0;
    for (size_t i = 0; i < n; i++) {
        sum += a[i] * b[i];
    }
    return sum;
}

// Vector operations for SIMD potential
EXPORT void vector_add(const double* a, const double* b, double* c, size_t n) {
    for (size_t i = 0; i < n; i++) {
        c[i] = a[i] + b[i];
    }
}

EXPORT double vector_norm(const double* v, size_t n) {
    double sum = 0.0;
    for (size_t i = 0; i < n; i++) {
        sum += v[i] * v[i];
    }
    return sqrt(sum);
}

// =============================================================================
// 9. Additional Test Functions
// =============================================================================

// Multi-argument functions for argument passing overhead
EXPORT int sum_5_ints(int a, int b, int c, int d, int e) {
    return a + b + c + d + e;
}

EXPORT double sum_8_doubles(double a, double b, double c, double d,
                           double e, double f, double g, double h) {
    return a + b + c + d + e + f + g + h;
}

// Mixed argument types
EXPORT double mixed_args(int32_t i1, double d1, int64_t i2, float f1,
                        bool b1, double d2) {
    return i1 + d1 + i2 + f1 + (b1 ? 1.0 : 0.0) + d2;
}

// Large return values
typedef struct {
    double values[16];
} LargeReturn;

EXPORT LargeReturn create_large_return() {
    LargeReturn ret;
    for (int i = 0; i < 16; i++) {
        ret.values[i] = i * 1.1;
    }
    return ret;
}

// Function to verify library loading
EXPORT const char* get_library_version() {
    return "benchlib v1.0.0";
}