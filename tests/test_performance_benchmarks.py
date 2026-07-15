"""Performance benchmark tests for critical game logic operations.

These tests measure the actual performance of key operations to identify
bottlenecks and track improvements.
"""

import time
import statistics
from pathlib import Path

import pytest

from muara.engine.state import GameState
from muara.engine.chapter_loader import load_chapter, load_all_chapters
from muara.models.save_state import SaveState


def _make_state(flags: dict[str, bool | str | int] | None = None) -> GameState:
    """Create a GameState for benchmarking."""
    return GameState(SaveState(
        save_id="benchmark",
        current_chapter="test",
        current_scene="test",
        flags=flags or {},
    ))


def _benchmark(func, iterations: int = 1000) -> dict:
    """Run a benchmark and return timing statistics."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        "iterations": iterations,
        "total_s": sum(times),
        "mean_ms": statistics.mean(times) * 1000,
        "median_ms": statistics.median(times) * 1000,
        "min_ms": min(times) * 1000,
        "max_ms": max(times) * 1000,
        "stdev_ms": statistics.stdev(times) * 1000 if len(times) > 1 else 0,
    }


class TestConditionEvaluationBenchmark:
    """Benchmark tests for evaluate_condition()."""
    
    def test_benchmark_truthy_check(self):
        """Benchmark simple truthy check."""
        state = _make_state({"melapor": True})
        result = _benchmark(lambda: state.evaluate_condition("melapor"))
        assert result["mean_ms"] < 100, f"Truthy check too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_equality_check(self):
        """Benchmark equality check."""
        state = _make_state({"chapter_5_choice": "simpan"})
        result = _benchmark(lambda: state.evaluate_condition("chapter_5_choice == simpan"))
        assert result["mean_ms"] < 100, f"Equality check too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_numeric_comparison(self):
        """Benchmark numeric comparison."""
        state = _make_state({"skor": 10})
        result = _benchmark(lambda: state.evaluate_condition("skor >= 5"))
        assert result["mean_ms"] < 100, f"Numeric comparison too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_negation(self):
        """Benchmark negation."""
        state = _make_state({"melapor": True})
        result = _benchmark(lambda: state.evaluate_condition("not melapor"))
        assert result["mean_ms"] < 100, f"Negation too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_complex_condition(self):
        """Benchmark complex condition with multiple operators."""
        state = _make_state({
            "chapter": 4,
            "trust_level": 3,
            "melapor": True,
        })
        result = _benchmark(lambda: state.evaluate_condition("chapter == 4"))
        assert result["mean_ms"] < 100, f"Complex condition too slow: {result['mean_ms']:.2f}ms"


class TestFlagOperationsBenchmark:
    """Benchmark tests for flag operations."""
    
    def test_benchmark_set_flag(self):
        """Benchmark set_flag operation."""
        state = _make_state()
        result = _benchmark(lambda: state.set_flag("test_flag", True))
        assert result["mean_ms"] < 50, f"set_flag too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_get_flag(self):
        """Benchmark get_flag operation."""
        state = _make_state({"test_flag": True})
        result = _benchmark(lambda: state.get_flag("test_flag"))
        assert result["mean_ms"] < 50, f"get_flag too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_increment_counter(self):
        """Benchmark increment_counter operation."""
        state = _make_state({"counter": 0})
        result = _benchmark(lambda: state.increment_counter("counter"))
        assert result["mean_ms"] < 50, f"increment_counter too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_add_to_set(self):
        """Benchmark add_to_set operation."""
        state = _make_state()
        result = _benchmark(lambda: state.add_to_set("my_set", "item1"))
        assert result["mean_ms"] < 50, f"add_to_set too slow: {result['mean_ms']:.2f}ms"


class TestChapterLoadingBenchmark:
    """Benchmark tests for chapter loading."""
    
    def test_benchmark_load_single_chapter(self):
        """Benchmark loading a single chapter."""
        content_dir = Path(__file__).parent.parent / "content" / "chapters"
        if not content_dir.exists():
            pytest.skip("Content directory not found")
        
        chapters = list(content_dir.glob("*.yaml"))
        if not chapters:
            pytest.skip("No chapters found")
        
        chapter_file = chapters[0]
        result = _benchmark(lambda: load_chapter(chapter_file))
        assert result["mean_ms"] < 500, f"Chapter loading too slow: {result['mean_ms']:.2f}ms"
    
    def test_benchmark_load_all_chapters(self):
        """Benchmark loading all chapters."""
        chapters_dir = Path(__file__).parent.parent / "content" / "chapters"
        if not chapters_dir.exists():
            pytest.skip("Chapters directory not found")
        
        result = _benchmark(lambda: load_all_chapters(chapters_dir), iterations=10)
        assert result["mean_ms"] < 2000, f"Loading all chapters too slow: {result['mean_ms']:.2f}ms"


class TestEventSchedulingBenchmark:
    """Benchmark tests for event scheduling."""
    
    def test_benchmark_evaluate_condition_in_event(self):
        """Benchmark condition evaluation in event context."""
        state = _make_state({
            "world_day": 3,
            "world_shift": "pagi",
            "trust_jaya": 2,
        })
        result = _benchmark(lambda: state.evaluate_condition("world_day >= 3"))
        assert result["mean_ms"] < 200, f"Event condition evaluation too slow: {result['mean_ms']:.2f}ms"


def test_performance_summary():
    """Print a summary of all performance benchmarks."""
    state = _make_state({
        "melapor": True,
        "chapter_5_choice": "simpan",
        "skor": 10,
        "chapter": 4,
    })
    
    benchmarks = {
        "truthy_check": _benchmark(lambda: state.evaluate_condition("melapor")),
        "equality_check": _benchmark(lambda: state.evaluate_condition("chapter_5_choice == simpan")),
        "numeric_comparison": _benchmark(lambda: state.evaluate_condition("skor >= 5")),
        "set_flag": _benchmark(lambda: state.set_flag("new_flag", True)),
        "get_flag": _benchmark(lambda: state.get_flag("melapor")),
    }
    
    print("\n=== Performance Benchmark Summary ===")
    for name, stats in benchmarks.items():
        print(f"{name:25s}: {stats['mean_ms']:8.3f}ms (mean)")
    print("=" * 45)
