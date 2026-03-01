"""Extended unit tests for observability module.

Covers RAGMetrics and MetricsTracker thoroughly, including edge cases
such as None tokens, empty tracker stats, and copy isolation in get_all().
"""

import time

import pytest

from vibe_rag.utils.observability import MetricsTracker, RAGMetrics


# ---------------------------------------------------------------------------
# Tests: RAGMetrics dataclass
# ---------------------------------------------------------------------------


class TestRAGMetricsDefaults:
    """Tests for RAGMetrics default values."""

    def test_query_defaults_to_empty_string(self):
        """query field defaults to empty string."""
        m = RAGMetrics()
        assert m.query == ""

    def test_answer_defaults_to_empty_string(self):
        """answer field defaults to empty string."""
        m = RAGMetrics()
        assert m.answer == ""

    def test_retrieval_time_ms_defaults_to_zero(self):
        """retrieval_time_ms defaults to 0.0."""
        m = RAGMetrics()
        assert m.retrieval_time_ms == 0.0

    def test_generation_time_ms_defaults_to_zero(self):
        """generation_time_ms defaults to 0.0."""
        m = RAGMetrics()
        assert m.generation_time_ms == 0.0

    def test_total_time_ms_defaults_to_zero(self):
        """total_time_ms defaults to 0.0."""
        m = RAGMetrics()
        assert m.total_time_ms == 0.0

    def test_documents_retrieved_defaults_to_zero(self):
        """documents_retrieved defaults to 0."""
        m = RAGMetrics()
        assert m.documents_retrieved == 0

    def test_documents_used_defaults_to_zero(self):
        """documents_used defaults to 0."""
        m = RAGMetrics()
        assert m.documents_used == 0

    def test_input_tokens_defaults_to_none(self):
        """input_tokens defaults to None (not tracked)."""
        m = RAGMetrics()
        assert m.input_tokens is None

    def test_output_tokens_defaults_to_none(self):
        """output_tokens defaults to None (not tracked)."""
        m = RAGMetrics()
        assert m.output_tokens is None

    def test_metadata_defaults_to_empty_dict(self):
        """metadata defaults to an empty dict."""
        m = RAGMetrics()
        assert m.metadata == {}


class TestRAGMetricsQueryId:
    """Tests for RAGMetrics auto-generated query_id."""

    def test_query_id_is_auto_generated(self):
        """query_id is auto-generated as a non-empty string."""
        m = RAGMetrics()
        assert m.query_id is not None
        assert len(m.query_id) > 0

    def test_query_id_is_unique_per_instance(self):
        """Each RAGMetrics instance receives a unique query_id."""
        ids = {RAGMetrics().query_id for _ in range(20)}
        assert len(ids) == 20, "Expected 20 unique query IDs for 20 instances"

    def test_query_id_can_be_overridden(self):
        """query_id can be set explicitly."""
        m = RAGMetrics(query_id="fixed-id-abc")
        assert m.query_id == "fixed-id-abc"


class TestRAGMetricsToDict:
    """Tests for RAGMetrics.to_dict()."""

    def test_to_dict_returns_dict(self):
        """to_dict() returns a dictionary."""
        m = RAGMetrics()
        result = m.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_all_expected_fields(self):
        """to_dict() includes every expected key."""
        m = RAGMetrics()
        result = m.to_dict()
        expected_keys = {
            "query_id",
            "query",
            "answer",
            "retrieval_time_ms",
            "generation_time_ms",
            "total_time_ms",
            "documents_retrieved",
            "documents_used",
            "input_tokens",
            "output_tokens",
            "metadata",
        }
        assert set(result.keys()) == expected_keys

    def test_to_dict_values_match_fields(self):
        """to_dict() values match the corresponding dataclass fields."""
        m = RAGMetrics(
            query_id="test-id",
            query="What is RAG?",
            answer="RAG stands for Retrieval-Augmented Generation.",
            retrieval_time_ms=12.5,
            generation_time_ms=45.0,
            total_time_ms=60.0,
            documents_retrieved=5,
            documents_used=3,
            input_tokens=100,
            output_tokens=50,
        )
        result = m.to_dict()
        assert result["query_id"] == "test-id"
        assert result["query"] == "What is RAG?"
        assert result["answer"] == "RAG stands for Retrieval-Augmented Generation."
        assert result["retrieval_time_ms"] == 12.5
        assert result["generation_time_ms"] == 45.0
        assert result["total_time_ms"] == 60.0
        assert result["documents_retrieved"] == 5
        assert result["documents_used"] == 3
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50

    def test_to_dict_none_tokens_included(self):
        """to_dict() includes None values for untracked token fields."""
        m = RAGMetrics()
        result = m.to_dict()
        assert result["input_tokens"] is None
        assert result["output_tokens"] is None

    def test_to_dict_includes_metadata(self):
        """to_dict() includes the metadata dict."""
        m = RAGMetrics()
        m.metadata["key"] = "value"
        result = m.to_dict()
        assert result["metadata"] == {"key": "value"}


class TestRAGMetricsSummarize:
    """Tests for RAGMetrics.summarize()."""

    def test_summarize_returns_string(self):
        """summarize() returns a string."""
        m = RAGMetrics()
        assert isinstance(m.summarize(), str)

    def test_summarize_contains_query_id(self):
        """summarize() output includes the query_id."""
        m = RAGMetrics(query_id="abc-123")
        summary = m.summarize()
        assert "abc-123" in summary

    def test_summarize_contains_total_time(self):
        """summarize() output includes the total_time_ms value."""
        m = RAGMetrics(total_time_ms=123.45)
        summary = m.summarize()
        assert "123.45" in summary

    def test_summarize_contains_retrieval_time(self):
        """summarize() output includes retrieval timing info."""
        m = RAGMetrics(retrieval_time_ms=50.0, documents_retrieved=3)
        summary = m.summarize()
        assert "50.00" in summary
        assert "3" in summary

    def test_summarize_contains_generation_time(self):
        """summarize() output includes the generation_time_ms value."""
        m = RAGMetrics(generation_time_ms=75.0)
        summary = m.summarize()
        assert "75.00" in summary

    def test_summarize_shows_na_for_none_tokens(self):
        """summarize() shows 'N/A' when tokens are not tracked."""
        m = RAGMetrics()
        summary = m.summarize()
        assert "N/A" in summary

    def test_summarize_shows_token_counts_when_set(self):
        """summarize() shows numeric token counts when they are set."""
        m = RAGMetrics(input_tokens=200, output_tokens=50)
        summary = m.summarize()
        assert "200" in summary
        assert "50" in summary


# ---------------------------------------------------------------------------
# Tests: MetricsTracker
# ---------------------------------------------------------------------------


class TestMetricsTrackerCreateMetrics:
    """Tests for MetricsTracker.create_metrics()."""

    def test_create_metrics_returns_rag_metrics(self):
        """create_metrics() returns a RAGMetrics instance."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("test query")
        assert isinstance(m, RAGMetrics)

    def test_create_metrics_sets_query_field(self):
        """create_metrics() sets the query field on the returned object."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("What is Python?")
        assert m.query == "What is Python?"

    def test_create_metrics_sets_created_at_in_metadata(self):
        """create_metrics() adds 'created_at' timestamp to metadata."""
        before = time.time()
        tracker = MetricsTracker()
        m = tracker.create_metrics("query")
        after = time.time()

        assert "created_at" in m.metadata
        assert before <= m.metadata["created_at"] <= after

    def test_create_metrics_does_not_record_automatically(self):
        """create_metrics() does not add metrics to the tracker's internal list."""
        tracker = MetricsTracker()
        tracker.create_metrics("query")
        assert len(tracker.get_all()) == 0


class TestMetricsTrackerRecord:
    """Tests for MetricsTracker.record()."""

    def test_record_stores_metrics(self):
        """record() adds the metrics object to the tracker."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("question")
        tracker.record(m)
        assert len(tracker.get_all()) == 1

    def test_record_sets_recorded_at_in_metadata(self):
        """record() adds 'recorded_at' timestamp to metadata."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("question")

        before = time.time()
        tracker.record(m)
        after = time.time()

        assert "recorded_at" in m.metadata
        assert before <= m.metadata["recorded_at"] <= after

    def test_record_multiple_metrics(self):
        """Multiple record() calls accumulate correctly."""
        tracker = MetricsTracker()
        for i in range(5):
            m = tracker.create_metrics(f"query {i}")
            tracker.record(m)
        assert len(tracker.get_all()) == 5


class TestMetricsTrackerGetAll:
    """Tests for MetricsTracker.get_all()."""

    def test_get_all_returns_list(self):
        """get_all() returns a list."""
        tracker = MetricsTracker()
        result = tracker.get_all()
        assert isinstance(result, list)

    def test_get_all_empty_initially(self):
        """get_all() returns an empty list before any records."""
        tracker = MetricsTracker()
        assert tracker.get_all() == []

    def test_get_all_returns_copy(self):
        """get_all() returns a copy — mutating it does not affect the tracker."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("query")
        tracker.record(m)

        result = tracker.get_all()
        result.clear()  # Mutate the returned copy

        # The internal list should be unaffected
        assert len(tracker.get_all()) == 1

    def test_get_all_preserves_insertion_order(self):
        """get_all() returns metrics in the order they were recorded."""
        tracker = MetricsTracker()
        queries = ["first", "second", "third"]
        for q in queries:
            m = tracker.create_metrics(q)
            tracker.record(m)

        results = tracker.get_all()
        assert [r.query for r in results] == queries


class TestMetricsTrackerGetStats:
    """Tests for MetricsTracker.get_stats()."""

    def test_get_stats_empty_tracker_returns_zeros(self):
        """get_stats() with no recorded metrics returns a dict of zeros."""
        tracker = MetricsTracker()
        stats = tracker.get_stats()

        assert stats["total_queries"] == 0
        assert stats["avg_total_time_ms"] == 0.0
        assert stats["avg_retrieval_time_ms"] == 0.0
        assert stats["avg_generation_time_ms"] == 0.0
        assert stats["avg_documents_retrieved"] == 0.0
        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0

    def test_get_stats_correct_averages_with_three_metrics(self):
        """get_stats() computes correct averages across 3 recorded metrics."""
        tracker = MetricsTracker()

        data = [
            dict(total_time_ms=100.0, retrieval_time_ms=20.0, generation_time_ms=80.0, documents_retrieved=3),
            dict(total_time_ms=200.0, retrieval_time_ms=40.0, generation_time_ms=160.0, documents_retrieved=5),
            dict(total_time_ms=300.0, retrieval_time_ms=60.0, generation_time_ms=240.0, documents_retrieved=7),
        ]

        for d in data:
            m = RAGMetrics(**d)
            tracker.record(m)

        stats = tracker.get_stats()
        assert stats["total_queries"] == 3
        assert abs(stats["avg_total_time_ms"] - 200.0) < 1e-9
        assert abs(stats["avg_retrieval_time_ms"] - 40.0) < 1e-9
        assert abs(stats["avg_generation_time_ms"] - 160.0) < 1e-9
        assert abs(stats["avg_documents_retrieved"] - 5.0) < 1e-9

    def test_get_stats_none_tokens_ignored_in_sum(self):
        """get_stats() sums only non-None token counts (ignores None entries)."""
        tracker = MetricsTracker()

        # m1: tokens tracked
        m1 = RAGMetrics(input_tokens=100, output_tokens=50)
        tracker.record(m1)

        # m2: tokens NOT tracked (None)
        m2 = RAGMetrics()  # input_tokens=None, output_tokens=None
        tracker.record(m2)

        # m3: tokens tracked
        m3 = RAGMetrics(input_tokens=200, output_tokens=75)
        tracker.record(m3)

        stats = tracker.get_stats()
        # Only m1 and m3 contribute to totals
        assert stats["total_input_tokens"] == 300
        assert stats["total_output_tokens"] == 125

    def test_get_stats_all_none_tokens_sums_to_zero(self):
        """get_stats() yields 0 for total tokens when all entries have None tokens."""
        tracker = MetricsTracker()
        for _ in range(3):
            tracker.record(RAGMetrics())

        stats = tracker.get_stats()
        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0

    def test_get_stats_single_metric(self):
        """get_stats() with a single metric computes correct stats."""
        tracker = MetricsTracker()
        m = RAGMetrics(
            total_time_ms=50.0,
            retrieval_time_ms=10.0,
            generation_time_ms=40.0,
            documents_retrieved=2,
            input_tokens=80,
            output_tokens=30,
        )
        tracker.record(m)

        stats = tracker.get_stats()
        assert stats["total_queries"] == 1
        assert stats["avg_total_time_ms"] == 50.0
        assert stats["avg_retrieval_time_ms"] == 10.0
        assert stats["avg_generation_time_ms"] == 40.0
        assert stats["avg_documents_retrieved"] == 2.0
        assert stats["total_input_tokens"] == 80
        assert stats["total_output_tokens"] == 30


class TestMetricsTrackerClear:
    """Tests for MetricsTracker.clear()."""

    def test_clear_removes_all_metrics(self):
        """clear() removes all recorded metrics from the tracker."""
        tracker = MetricsTracker()
        for _ in range(5):
            m = tracker.create_metrics("query")
            tracker.record(m)

        assert len(tracker.get_all()) == 5

        tracker.clear()

        assert len(tracker.get_all()) == 0

    def test_clear_on_empty_tracker_does_not_raise(self):
        """clear() on an empty tracker is a no-op and does not raise."""
        tracker = MetricsTracker()
        tracker.clear()  # Should not raise
        assert tracker.get_all() == []

    def test_get_stats_after_clear_returns_zeros(self):
        """get_stats() returns zeros after clear() empties the tracker."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("query")
        m.total_time_ms = 999.0
        tracker.record(m)

        tracker.clear()
        stats = tracker.get_stats()
        assert stats["total_queries"] == 0
        assert stats["avg_total_time_ms"] == 0.0

    def test_can_record_after_clear(self):
        """Tracker can accept new records after clear()."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("before clear")
        tracker.record(m)
        tracker.clear()

        m2 = tracker.create_metrics("after clear")
        tracker.record(m2)

        results = tracker.get_all()
        assert len(results) == 1
        assert results[0].query == "after clear"
