/*
 * pybind11_wrapper.cpp - pybind11 Python bindings for benchlib
 * 
 * This file creates Python bindings for the benchmark C library using pybind11.
 * Provides equivalent functionality to ctypes/cffi for fair performance comparison.
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

// Include the original benchlib header functionality
extern "C" {
    // Forward declarations for benchlib functions
    void noop();
    int return_int();
    int add_int32(int a, int b);
    long long add_int64(long long a, long long b);
    unsigned long long add_uint64(unsigned long long a, unsigned long long b);
    bool logical_and(bool a, bool b);
    bool logical_or(bool a, bool b);
    bool logical_not(bool a);
    float add_float(float a, float b);
    double add_double(double a, double b);
    double multiply_double(double a, double b);
    
    // Array operations
    double sum_doubles_readonly(const double* arr, size_t n);
    void scale_doubles_inplace(double* arr, size_t n, double factor);
    int sum_int32_array(const int* arr, size_t n);
    void fill_int32_array(int* arr, size_t n, int value);
    
    // String operations
    size_t bytes_length(const char* data, size_t len);
    size_t utf8_length(const char* str);
    const char* string_identity(const char* s);
    char* string_concat(const char* a, const char* b);
    void free_string(char* s);
    
    // Structure operations
    typedef struct {
        int x;
        int y;
        double value;
    } SimpleStruct;
    
    SimpleStruct create_simple(int x, int y, double value);
    double sum_simple(const SimpleStruct* s);
    void modify_simple(SimpleStruct* s, double new_value);
    
    // Callback operations
    int apply_callback(int x, int (*transform)(int));
    int c_transform(int x);
    
    // Matrix operations
    void matrix_multiply_naive(const double* a, const double* b, double* c,
                              size_t m, size_t n, size_t k);
    double dot_product(const double* a, const double* b, size_t n);
    void vector_add(const double* a, const double* b, double* c, size_t n);
    double vector_norm(const double* v, size_t n);
}

namespace py = pybind11;

// Wrapper functions for better pybind11 integration

// Array operation wrappers
double sum_doubles_readonly_wrapper(py::array_t<double> input) {
    py::buffer_info buf_info = input.request();
    
    if (buf_info.ndim != 1) {
        throw std::runtime_error("Input array must be 1-dimensional");
    }
    
    const double* ptr = static_cast<const double*>(buf_info.ptr);
    size_t size = buf_info.shape[0];
    
    return sum_doubles_readonly(ptr, size);
}

void scale_doubles_inplace_wrapper(py::array_t<double> input, double factor) {
    py::buffer_info buf_info = input.request();
    
    if (buf_info.ndim != 1) {
        throw std::runtime_error("Input array must be 1-dimensional");
    }
    
    double* ptr = static_cast<double*>(buf_info.ptr);
    size_t size = buf_info.shape[0];
    
    scale_doubles_inplace(ptr, size, factor);
}

int sum_int32_array_wrapper(py::array_t<int> input) {
    py::buffer_info buf_info = input.request();
    
    if (buf_info.ndim != 1) {
        throw std::runtime_error("Input array must be 1-dimensional");
    }
    
    const int* ptr = static_cast<const int*>(buf_info.ptr);
    size_t size = buf_info.shape[0];
    
    return sum_int32_array(ptr, size);
}

void fill_int32_array_wrapper(py::array_t<int> input, int value) {
    py::buffer_info buf_info = input.request();
    
    if (buf_info.ndim != 1) {
        throw std::runtime_error("Input array must be 1-dimensional");
    }
    
    int* ptr = static_cast<int*>(buf_info.ptr);
    size_t size = buf_info.shape[0];
    
    fill_int32_array(ptr, size, value);
}

// Matrix operation wrappers
void matrix_multiply_naive_wrapper(py::array_t<double> a, py::array_t<double> b, py::array_t<double> c,
                                  size_t m, size_t n, size_t k) {
    py::buffer_info a_info = a.request();
    py::buffer_info b_info = b.request();
    py::buffer_info c_info = c.request();
    
    if (a_info.ndim != 2 || b_info.ndim != 2 || c_info.ndim != 2) {
        throw std::runtime_error("All matrices must be 2-dimensional");
    }
    
    const double* a_ptr = static_cast<const double*>(a_info.ptr);
    const double* b_ptr = static_cast<const double*>(b_info.ptr);
    double* c_ptr = static_cast<double*>(c_info.ptr);
    
    matrix_multiply_naive(a_ptr, b_ptr, c_ptr, m, n, k);
}

double dot_product_wrapper(py::array_t<double> a, py::array_t<double> b) {
    py::buffer_info a_info = a.request();
    py::buffer_info b_info = b.request();
    
    if (a_info.ndim != 1 || b_info.ndim != 1) {
        throw std::runtime_error("Input arrays must be 1-dimensional");
    }
    
    if (a_info.shape[0] != b_info.shape[0]) {
        throw std::runtime_error("Arrays must have the same length");
    }
    
    const double* a_ptr = static_cast<const double*>(a_info.ptr);
    const double* b_ptr = static_cast<const double*>(b_info.ptr);
    size_t n = a_info.shape[0];
    
    return dot_product(a_ptr, b_ptr, n);
}

void vector_add_wrapper(py::array_t<double> a, py::array_t<double> b, py::array_t<double> c) {
    py::buffer_info a_info = a.request();
    py::buffer_info b_info = b.request();
    py::buffer_info c_info = c.request();
    
    if (a_info.ndim != 1 || b_info.ndim != 1 || c_info.ndim != 1) {
        throw std::runtime_error("All arrays must be 1-dimensional");
    }
    
    auto n = a_info.shape[0];
    if (b_info.shape[0] != n || c_info.shape[0] != n) {
        throw std::runtime_error("All arrays must have the same length");
    }
    
    const double* a_ptr = static_cast<const double*>(a_info.ptr);
    const double* b_ptr = static_cast<const double*>(b_info.ptr);
    double* c_ptr = static_cast<double*>(c_info.ptr);
    
    vector_add(a_ptr, b_ptr, c_ptr, static_cast<size_t>(n));
}

double vector_norm_wrapper(py::array_t<double> v) {
    py::buffer_info v_info = v.request();
    
    if (v_info.ndim != 1) {
        throw std::runtime_error("Input array must be 1-dimensional");
    }
    
    const double* v_ptr = static_cast<const double*>(v_info.ptr);
    size_t n = v_info.shape[0];
    
    return vector_norm(v_ptr, n);
}

// Callback wrapper - allow Python functions as callbacks
int apply_callback_wrapper(int x, std::function<int(int)> transform) {
    return transform(x);
}

// String operation wrappers
size_t bytes_length_wrapper(py::bytes data, size_t len) {
    std::string str_data = data;
    return bytes_length(str_data.c_str(), len);
}

size_t utf8_length_wrapper(py::bytes data) {
    std::string str_data = data;
    return utf8_length(str_data.c_str());
}

std::string string_concat_wrapper(py::bytes a, py::bytes b) {
    std::string str_a = a;
    std::string str_b = b;
    char* result = string_concat(str_a.c_str(), str_b.c_str());
    if (result) {
        std::string ret(result);
        free_string(result);
        return ret;
    }
    return "";
}

void free_string_wrapper(char*) {
    // No-op for pybind11 - memory managed automatically
}

std::string string_identity_wrapper(const std::string& s) {
    return std::string(string_identity(s.c_str()));
}

PYBIND11_MODULE(benchlib_pybind11, m) {
    m.doc() = "pybind11 bindings for FFI benchmark library";
    
    // Basic operations
    m.def("noop", &noop, "No-operation function");
    m.def("return_int", &return_int, "Return integer constant");
    
    // Integer operations
    m.def("add_int32", &add_int32, "Add two 32-bit integers");
    m.def("add_int64", &add_int64, "Add two 64-bit integers");
    m.def("add_uint64", &add_uint64, "Add two unsigned 64-bit integers");
    
    // Boolean operations
    m.def("logical_and", &logical_and, "Logical AND operation");
    m.def("logical_or", &logical_or, "Logical OR operation");
    m.def("logical_not", &logical_not, "Logical NOT operation");
    
    // Floating point operations
    m.def("add_float", &add_float, "Add two floats");
    m.def("add_double", &add_double, "Add two doubles");
    m.def("multiply_double", &multiply_double, "Multiply two doubles");
    
    // Array operations
    m.def("sum_doubles_readonly", &sum_doubles_readonly_wrapper, 
          "Sum array of doubles (read-only)", py::arg("input"));
    m.def("scale_doubles_inplace", &scale_doubles_inplace_wrapper,
          "Scale array of doubles in-place", py::arg("input"), py::arg("factor"));
    m.def("sum_int32_array", &sum_int32_array_wrapper,
          "Sum array of 32-bit integers", py::arg("input"));
    m.def("fill_int32_array", &fill_int32_array_wrapper,
          "Fill array with value", py::arg("input"), py::arg("value"));
    
    // String operations
    m.def("bytes_length", &bytes_length_wrapper, "Get byte length of string");
    m.def("utf8_length", &utf8_length_wrapper, "Get UTF-8 character count");
    m.def("string_identity", &string_identity_wrapper, "String identity function");
    
    // Structure operations
    py::class_<SimpleStruct>(m, "SimpleStruct")
        .def(py::init<>())
        .def_readwrite("x", &SimpleStruct::x)
        .def_readwrite("y", &SimpleStruct::y)
        .def_readwrite("value", &SimpleStruct::value);
    
    m.def("create_simple", &create_simple, "Create SimpleStruct");
    m.def("sum_simple", &sum_simple, "Sum SimpleStruct fields");
    m.def("modify_simple", &modify_simple, "Modify SimpleStruct value");
    
    // Callback operations
    m.def("apply_callback", &apply_callback_wrapper, 
          "Apply callback function", py::arg("x"), py::arg("transform"));
    m.def("c_transform", &c_transform, "C transform function");
    
    // Matrix operations
    m.def("matrix_multiply_naive", &matrix_multiply_naive_wrapper,
          "Naive matrix multiplication", 
          py::arg("a"), py::arg("b"), py::arg("c"), py::arg("m"), py::arg("n"), py::arg("k"));
    m.def("dot_product", &dot_product_wrapper,
          "Dot product of two vectors", py::arg("a"), py::arg("b"));
    m.def("vector_add", &vector_add_wrapper,
          "Vector addition", py::arg("a"), py::arg("b"), py::arg("c"));
    m.def("vector_norm", &vector_norm_wrapper,
          "Vector norm", py::arg("v"));
}