import pytest
from bitcoin_analyzer.analysis.metrics import PriceEstimator, build_spike_stencil, build_smooth_stencil

class TestPriceEstimator:
    def test_init(self):
        estimator = PriceEstimator()
        assert len(estimator.output_bins) > 0
        assert len(estimator.bin_counts) == len(estimator.output_bins)
        assert estimator.center == 601

    def test_add_output(self):
        estimator = PriceEstimator()
        initial_sum = sum(estimator.bin_counts)
        
        estimator.add_output(0.001)  # 1000 sats
        
        assert sum(estimator.bin_counts) > initial_sum

    def test_add_output_zero_or_negative(self):
        estimator = PriceEstimator()
        initial_sum = sum(estimator.bin_counts)
        
        estimator.add_output(0)
        estimator.add_output(-0.1)
        
        assert sum(estimator.bin_counts) == initial_sum

    def test_stencil_building(self):
        spike_stencil = build_spike_stencil()
        smooth_stencil = build_smooth_stencil()
        
        assert len(spike_stencil) == 803
        assert len(smooth_stencil) == 803
        assert spike_stencil[400] > 0  # Should have weight for $100