"""NLP performance benchmarks (optional)."""
import pytest
from src.nlp.message_processor import MessageProcessor


@pytest.mark.benchmark
def test_processor_throughput(benchmark, sample_text):
    p = MessageProcessor()
    result = benchmark(p.process, sample_text, include_explanations=False)
    assert "category" in result
