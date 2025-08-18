"""
Advanced Statistical Analysis for FFI Benchmarks.

Implements rigorous statistical methods following best practices from
"Statistics for the Analysis of Experimental Data" and recommendations
from performance analysis literature.

Key Features:
- Mann-Whitney U tests for non-parametric comparison
- Cliff's delta effect sizes for practical significance
- Bootstrap confidence intervals for robust estimation
- Multiple comparison corrections (Bonferroni, Benjamini-Hochberg)
- Power analysis and sample size calculation
"""

import numpy as np
import math
from typing import List, Dict, Tuple, Any, Optional, Union
from dataclasses import dataclass
from scipy import stats
from collections import defaultdict


@dataclass
class StatisticalTest:
    """Results from a statistical test."""
    test_name: str
    p_value: float
    effect_size: float
    effect_interpretation: str
    confidence_interval: Tuple[float, float]
    sample_sizes: Tuple[int, int]
    power: Optional[float] = None
    significant: bool = False
    practical_significance: bool = False


@dataclass
class ComparisonResult:
    """Complete comparison between two methods."""
    method1: str
    method2: str
    faster_method: str
    relative_performance: float
    statistical_test: StatisticalTest
    descriptive_stats: Dict[str, Any]


class AdvancedStatistics:
    """Advanced statistical analysis for FFI benchmark results."""
    
    def __init__(self, alpha: float = 0.05, effect_size_threshold: float = 0.2):
        """
        Initialize statistical analysis framework.
        
        Args:
            alpha: Significance level for hypothesis tests
            effect_size_threshold: Minimum effect size for practical significance
        """
        self.alpha = alpha
        self.effect_size_threshold = effect_size_threshold
        
    def mann_whitney_u_test(self, samples1: List[float], samples2: List[float], 
                           alternative: str = 'two-sided') -> Dict[str, Any]:
        """
        Perform Mann-Whitney U test for comparing two independent samples.
        
        Non-parametric test that doesn't assume normal distribution.
        More robust than t-test for performance data.
        
        Args:
            samples1: First sample (e.g., ctypes times)
            samples2: Second sample (e.g., cffi times) 
            alternative: 'two-sided', 'less', or 'greater'
            
        Returns:
            Dictionary containing test results
        """
        # Perform Mann-Whitney U test
        statistic, p_value = stats.mannwhitneyu(
            samples1, samples2, 
            alternative=alternative,
            use_continuity=True
        )
        
        # Calculate effect size (Cliff's delta)
        cliff_delta = self.cliff_delta(samples1, samples2)
        
        # Calculate confidence interval for median difference
        ci = self.bootstrap_median_difference_ci(samples1, samples2)
        
        return {
            'statistic': statistic,
            'p_value': p_value,
            'cliff_delta': cliff_delta,
            'effect_interpretation': self.interpret_cliff_delta(cliff_delta),
            'confidence_interval': ci,
            'sample_sizes': (len(samples1), len(samples2)),
            'significant': p_value < self.alpha,
            'practical_significance': abs(cliff_delta) >= self.effect_size_threshold
        }
    
    def cliff_delta(self, samples1: List[float], samples2: List[float]) -> float:
        """
        Calculate Cliff's delta effect size.
        
        Non-parametric effect size measure that indicates the probability
        that a randomly selected value from samples1 is greater than a
        randomly selected value from samples2.
        
        Args:
            samples1: First sample
            samples2: Second sample
            
        Returns:
            Cliff's delta value (-1 to 1)
        """
        n1, n2 = len(samples1), len(samples2)
        
        if n1 == 0 or n2 == 0:
            return 0.0
        
        # Count comparisons
        dominance = 0
        
        for x1 in samples1:
            for x2 in samples2:
                if x1 > x2:
                    dominance += 1
                elif x1 < x2:
                    dominance -= 1
                # Ties contribute 0
        
        return dominance / (n1 * n2)
    
    def interpret_cliff_delta(self, delta: float) -> str:
        """
        Interpret Cliff's delta magnitude following Cohen's conventions.
        
        Args:
            delta: Cliff's delta value
            
        Returns:
            Interpretation string
        """
        abs_delta = abs(delta)
        
        if abs_delta < 0.147:
            return "negligible"
        elif abs_delta < 0.33:
            return "small"
        elif abs_delta < 0.474:
            return "medium"
        else:
            return "large"
    
    def bootstrap_median_difference_ci(self, samples1: List[float], samples2: List[float],
                                     n_bootstrap: int = 10000, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Bootstrap confidence interval for median difference.
        
        Args:
            samples1: First sample
            samples2: Second sample
            n_bootstrap: Number of bootstrap resamples
            confidence: Confidence level
            
        Returns:
            (lower_bound, upper_bound) of confidence interval
        """
        np.random.seed(42)  # Reproducible results
        
        bootstrap_diffs = []
        n1, n2 = len(samples1), len(samples2)
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            resample1 = np.random.choice(samples1, size=n1, replace=True)
            resample2 = np.random.choice(samples2, size=n2, replace=True)
            
            # Calculate median difference
            diff = np.median(resample1) - np.median(resample2)
            bootstrap_diffs.append(diff)
        
        # Calculate percentile-based confidence interval
        alpha = 1 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_diffs, lower_percentile)
        ci_upper = np.percentile(bootstrap_diffs, upper_percentile)
        
        return (ci_lower, ci_upper)
    
    def descriptive_statistics(self, samples: List[float]) -> Dict[str, float]:
        """
        Calculate comprehensive descriptive statistics.
        
        Args:
            samples: List of sample values
            
        Returns:
            Dictionary of statistical measures
        """
        if not samples:
            return {}
        
        samples_array = np.array(samples)
        
        # Central tendency
        mean = np.mean(samples_array)
        median = np.median(samples_array)
        
        # Dispersion
        std = np.std(samples_array, ddof=1)
        var = np.var(samples_array, ddof=1)
        
        # Quartiles and IQR
        q25 = np.percentile(samples_array, 25)
        q75 = np.percentile(samples_array, 75)
        iqr = q75 - q25
        
        # Range
        min_val = np.min(samples_array)
        max_val = np.max(samples_array)
        range_val = max_val - min_val
        
        # Coefficient of variation
        cv = std / mean if mean != 0 else float('inf')
        
        # Skewness and kurtosis
        skewness = stats.skew(samples_array)
        kurtosis = stats.kurtosis(samples_array)
        
        # Median Absolute Deviation (robust measure of dispersion)
        mad = np.median(np.abs(samples_array - median))
        
        return {
            'count': len(samples),
            'mean': mean,
            'median': median,
            'std': std,
            'variance': var,
            'q25': q25,
            'q75': q75,
            'iqr': iqr,
            'min': min_val,
            'max': max_val,
            'range': range_val,
            'cv': cv,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'mad': mad
        }
    
    def compare_methods(self, method1_samples: List[float], method2_samples: List[float],
                       method1_name: str, method2_name: str) -> ComparisonResult:
        """
        Complete statistical comparison between two methods.
        
        Args:
            method1_samples: Performance samples from method 1
            method2_samples: Performance samples from method 2
            method1_name: Name of method 1
            method2_name: Name of method 2
            
        Returns:
            ComparisonResult object with complete analysis
        """
        # Perform Mann-Whitney U test
        test_result = self.mann_whitney_u_test(method1_samples, method2_samples)
        
        # Calculate descriptive statistics
        stats1 = self.descriptive_statistics(method1_samples)
        stats2 = self.descriptive_statistics(method2_samples)
        
        # Determine which method is faster (lower median = faster)
        median1 = stats1['median']
        median2 = stats2['median']
        
        if median1 < median2:
            faster_method = method1_name
            relative_performance = median2 / median1
        else:
            faster_method = method2_name
            relative_performance = median1 / median2
        
        # Create statistical test object
        statistical_test = StatisticalTest(
            test_name="Mann-Whitney U",
            p_value=test_result['p_value'],
            effect_size=test_result['cliff_delta'],
            effect_interpretation=test_result['effect_interpretation'],
            confidence_interval=test_result['confidence_interval'],
            sample_sizes=test_result['sample_sizes'],
            significant=test_result['significant'],
            practical_significance=test_result['practical_significance']
        )
        
        # Combine descriptive statistics
        descriptive_stats = {
            method1_name: stats1,
            method2_name: stats2,
            'median_difference': median1 - median2,
            'relative_difference_percent': ((median1 - median2) / median2) * 100 if median2 != 0 else float('inf')
        }
        
        return ComparisonResult(
            method1=method1_name,
            method2=method2_name,
            faster_method=faster_method,
            relative_performance=relative_performance,
            statistical_test=statistical_test,
            descriptive_stats=descriptive_stats
        )
    
    def multiple_comparisons_analysis(self, results: Dict[str, List[float]], 
                                    correction: str = 'bonferroni') -> Dict[str, Any]:
        """
        Perform multiple comparisons analysis with correction for Type I error.
        
        Args:
            results: Dictionary mapping method names to sample lists
            correction: 'bonferroni', 'benjamini-hochberg', or 'none'
            
        Returns:
            Dictionary containing pairwise comparisons and corrections
        """
        method_names = list(results.keys())
        n_methods = len(method_names)
        n_comparisons = n_methods * (n_methods - 1) // 2
        
        # Perform all pairwise comparisons
        comparisons = []
        p_values = []
        
        for i in range(n_methods):
            for j in range(i + 1, n_methods):
                method1 = method_names[i]
                method2 = method_names[j]
                
                comparison = self.compare_methods(
                    results[method1], results[method2], method1, method2
                )
                
                comparisons.append(comparison)
                p_values.append(comparison.statistical_test.p_value)
        
        # Apply multiple comparison correction
        if correction == 'bonferroni':
            corrected_alpha = self.alpha / n_comparisons
            corrected_p_values = [p * n_comparisons for p in p_values]
        elif correction == 'benjamini-hochberg':
            corrected_alpha, corrected_p_values = self._benjamini_hochberg_correction(p_values)
        else:
            corrected_alpha = self.alpha
            corrected_p_values = p_values
        
        # Update significance based on corrected values
        for i, comparison in enumerate(comparisons):
            comparison.statistical_test.significant = corrected_p_values[i] < corrected_alpha
        
        return {
            'comparisons': comparisons,
            'n_comparisons': n_comparisons,
            'correction_method': correction,
            'corrected_alpha': corrected_alpha,
            'original_p_values': p_values,
            'corrected_p_values': corrected_p_values,
            'significant_comparisons': sum(1 for c in comparisons if c.statistical_test.significant)
        }
    
    def _benjamini_hochberg_correction(self, p_values: List[float]) -> Tuple[float, List[float]]:
        """
        Apply Benjamini-Hochberg (FDR) correction for multiple comparisons.
        
        Args:
            p_values: List of original p-values
            
        Returns:
            (corrected_alpha, corrected_p_values)
        """
        n = len(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p_values = np.array(p_values)[sorted_indices]
        
        # Calculate corrected p-values
        corrected_p_values = np.zeros(n)
        for i in range(n):
            corrected_p_values[sorted_indices[i]] = sorted_p_values[i] * n / (i + 1)
        
        # Enforce monotonicity
        for i in range(n - 2, -1, -1):
            corrected_p_values[sorted_indices[i]] = min(
                corrected_p_values[sorted_indices[i]], 
                corrected_p_values[sorted_indices[i + 1]]
            )
        
        return self.alpha, corrected_p_values.tolist()
    
    def power_analysis(self, samples1: List[float], samples2: List[float], 
                      alpha: float = None) -> float:
        """
        Calculate statistical power for detecting difference between samples.
        
        Args:
            samples1: First sample
            samples2: Second sample
            alpha: Significance level (uses instance alpha if None)
            
        Returns:
            Statistical power (0-1)
        """
        if alpha is None:
            alpha = self.alpha
        
        # For Mann-Whitney U test power calculation
        # This is a simplified approximation
        n1, n2 = len(samples1), len(samples2)
        
        if n1 < 3 or n2 < 3:
            return 0.0
        
        # Calculate effect size
        cliff_delta = self.cliff_delta(samples1, samples2)
        
        # Approximate power calculation for Mann-Whitney U
        # Based on normal approximation
        n_harmonic = 2 * n1 * n2 / (n1 + n2)
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = abs(cliff_delta) * math.sqrt(n_harmonic / 12) - z_alpha
        power = stats.norm.cdf(z_beta)
        
        return max(0.0, min(1.0, power))
    
    def sample_size_calculation(self, effect_size: float, power: float = 0.8, 
                              alpha: float = None) -> int:
        """
        Calculate required sample size for desired power and effect size.
        
        Args:
            effect_size: Expected Cliff's delta effect size
            power: Desired statistical power
            alpha: Significance level (uses instance alpha if None)
            
        Returns:
            Required sample size per group
        """
        if alpha is None:
            alpha = self.alpha
        
        # Approximate sample size calculation for Mann-Whitney U
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        # Formula based on normal approximation
        n = ((z_alpha + z_beta) / effect_size) ** 2 * 12
        
        return max(3, int(math.ceil(n)))
    
    def generate_summary_report(self, multiple_comparison_results: Dict[str, Any]) -> str:
        """
        Generate a comprehensive statistical summary report.
        
        Args:
            multiple_comparison_results: Results from multiple_comparisons_analysis
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("FFI Benchmark Statistical Analysis Report")
        report.append("=" * 50)
        report.append("")
        
        # Overview
        comparisons = multiple_comparison_results['comparisons']
        n_comparisons = multiple_comparison_results['n_comparisons']
        significant_count = multiple_comparison_results['significant_comparisons']
        correction = multiple_comparison_results['correction_method']
        
        report.append(f"Analysis Overview:")
        report.append(f"  Total comparisons: {n_comparisons}")
        report.append(f"  Significant comparisons: {significant_count}")
        report.append(f"  Multiple comparison correction: {correction}")
        report.append(f"  Alpha level: {self.alpha}")
        report.append("")
        
        # Individual comparisons
        report.append("Pairwise Comparisons:")
        report.append("-" * 30)
        
        for comparison in comparisons:
            report.append(f"\n{comparison.method1} vs {comparison.method2}:")
            
            # Performance summary
            report.append(f"  Faster method: {comparison.faster_method}")
            report.append(f"  Performance advantage: {comparison.relative_performance:.2f}x")
            
            # Statistical test results
            test = comparison.statistical_test
            report.append(f"  Mann-Whitney U p-value: {test.p_value:.6f}")
            report.append(f"  Statistically significant: {'Yes' if test.significant else 'No'}")
            report.append(f"  Cliff's delta: {test.effect_size:.4f}")
            report.append(f"  Effect size: {test.effect_interpretation}")
            report.append(f"  Practically significant: {'Yes' if test.practical_significance else 'No'}")
            
            # Confidence interval
            ci_lower, ci_upper = test.confidence_interval
            report.append(f"  95% CI for median difference: [{ci_lower:.2f}, {ci_upper:.2f}]")
            
            # Sample sizes
            n1, n2 = test.sample_sizes
            report.append(f"  Sample sizes: {n1}, {n2}")
        
        # Summary of method rankings
        report.append("\nMethod Performance Ranking:")
        report.append("-" * 30)
        
        # Extract all methods and their median performance
        all_methods = set()
        for comparison in comparisons:
            all_methods.add(comparison.method1)
            all_methods.add(comparison.method2)
        
        method_performance = {}
        for comparison in comparisons:
            stats1 = comparison.descriptive_stats[comparison.method1]
            stats2 = comparison.descriptive_stats[comparison.method2]
            method_performance[comparison.method1] = stats1['median']
            method_performance[comparison.method2] = stats2['median']
        
        # Sort by median performance (lower = faster)
        sorted_methods = sorted(method_performance.items(), key=lambda x: x[1])
        
        for rank, (method, median_time) in enumerate(sorted_methods, 1):
            report.append(f"  {rank}. {method}: {median_time:.2f} ns median")
        
        return "\n".join(report)


def create_statistical_analyzer(alpha: float = 0.05, effect_size_threshold: float = 0.2) -> AdvancedStatistics:
    """Factory function to create statistical analyzer."""
    return AdvancedStatistics(alpha, effect_size_threshold)


if __name__ == "__main__":
    # Self-test with simulated data
    print("🧪 Testing statistical analysis framework...")
    
    stats_analyzer = create_statistical_analyzer()
    
    # Simulate performance data
    np.random.seed(42)
    
    # Method 1 (slower): mean=100ns, std=20ns
    method1_samples = np.random.normal(100, 20, 100).tolist()
    
    # Method 2 (faster): mean=80ns, std=15ns  
    method2_samples = np.random.normal(80, 15, 100).tolist()
    
    # Method 3 (fastest): mean=60ns, std=10ns
    method3_samples = np.random.normal(60, 10, 100).tolist()
    
    # Test single comparison
    print("\n1️⃣ Single Method Comparison:")
    comparison = stats_analyzer.compare_methods(
        method1_samples, method2_samples, "ctypes", "cffi"
    )
    
    print(f"Faster method: {comparison.faster_method}")
    print(f"Performance advantage: {comparison.relative_performance:.2f}x")
    print(f"P-value: {comparison.statistical_test.p_value:.6f}")
    print(f"Effect size: {comparison.statistical_test.effect_size:.4f} ({comparison.statistical_test.effect_interpretation})")
    
    # Test multiple comparisons
    print("\n2️⃣ Multiple Comparisons Analysis:")
    results = {
        'ctypes': method1_samples,
        'cffi': method2_samples,
        'pybind11': method3_samples
    }
    
    multiple_results = stats_analyzer.multiple_comparisons_analysis(results)
    print(f"Total comparisons: {multiple_results['n_comparisons']}")
    print(f"Significant comparisons: {multiple_results['significant_comparisons']}")
    
    # Generate summary report
    print("\n3️⃣ Summary Report:")
    report = stats_analyzer.generate_summary_report(multiple_results)
    print(report)
    
    print("\n✅ Statistical analysis test completed!")