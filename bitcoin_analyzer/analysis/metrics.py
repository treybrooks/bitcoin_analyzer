from typing import List, Tuple, Dict
from math import log10

class PriceEstimator:
    """Estimate Bitcoin price from transaction output distributions."""
    
    def __init__(self):
        # Bell curve parameters
        self.first_bin_value = -6
        self.last_bin_value = 6
        self.bins_per_10x = 200
        
        # Initialize bins and stencils
        self._init_bins()
        self._init_stencils()
        
    def _init_bins(self):
        """Initialize output bell curve bins."""
        self.output_bins = [0.0]
        
        for exponent in range(-6, 6):
            for b in range(0, 200):
                bin_value = 10 ** (exponent + b/200)
                self.output_bins.append(bin_value)
                
        self.num_bins = len(self.output_bins)
        self.bin_counts = [0.0] * self.num_bins
        
    def _init_stencils(self):
        """Initialize smooth and spike stencils for price detection."""
        # Smooth stencil - Gaussian-like
        num_elements = 803
        mean = 411
        std_dev = 201
        
        self.smooth_stencil = []
        for x in range(num_elements):
            exp_part = -((x - mean) ** 2) / (2 * (std_dev ** 2))
            self.smooth_stencil.append( (.00150 * 2.718281828459045 ** exp_part) + (.0000005 * x) )
            
        # Spike stencil - USD round amounts
        self.spike_stencil = []
        for n in range(0,803):
            self.spike_stencil.append(0.0)
        
        # Popular USD amounts and their weights
        self.spike_stencil[40] = 0.001300198324984352  # $1
        self.spike_stencil[141]= 0.001676746949820743  # $5
        self.spike_stencil[201]= 0.003468805546942046  # $10
        self.spike_stencil[202]= 0.001991977522512513  # 
        self.spike_stencil[236]= 0.001905066647961839  # $15
        self.spike_stencil[261]= 0.003341772718156079  # $20
        self.spike_stencil[262]= 0.002588902624584287  # 
        self.spike_stencil[296]= 0.002577893841190244  # $30
        self.spike_stencil[297]= 0.002733728814200412  # 
        self.spike_stencil[340]= 0.003076117748975647  # $50
        self.spike_stencil[341]= 0.005613067550103145  # 
        self.spike_stencil[342]= 0.003088253178535568  # 
        self.spike_stencil[400]= 0.002918457489366139  # $100
        self.spike_stencil[401]= 0.006174500465286022  # 
        self.spike_stencil[402]= 0.004417068070043504  # 
        self.spike_stencil[403]= 0.002628663628020371  # 
        self.spike_stencil[436]= 0.002858828161543839  # $150
        self.spike_stencil[461]= 0.004097463611984264  # $200
        self.spike_stencil[462]= 0.003345917406120509  # 
        self.spike_stencil[496]= 0.002521467726855856  # $300
        self.spike_stencil[497]= 0.002784125730361008  # 
        self.spike_stencil[541]= 0.003792850444811335  # $500
        self.spike_stencil[601]= 0.003688240815848247  # $1000
        self.spike_stencil[602]= 0.002392400117402263  # 
        self.spike_stencil[636]= 0.001280993059008106  # $1500
        self.spike_stencil[661]= 0.001654665137536031  # $2000
        self.spike_stencil[662]= 0.001395501347054946  # 
        self.spike_stencil[741]= 0.001154279140906312  # $5000
        self.spike_stencil[801]= 0.000832244504868709  # $10000
            
    def add_output(self, amount_btc: float):
        """Add a transaction output to the distribution."""
        if amount_btc <= 0:
            return
            
        amount_log = log10(amount_btc)
        percent_in_range = (amount_log - self.first_bin_value) / (self.last_bin_value - self.first_bin_value)
        bin_number_est = int(percent_in_range * self.num_bins)
        
        if 0 <= bin_number_est < self.num_bins - 1:
            while bin_number_est < self.num_bins - 1 and self.output_bins[bin_number_est] <= amount_btc:
                bin_number_est += 1
            self.bin_counts[bin_number_est - 1] += 1.0
            
    def estimate_price(self) -> Tuple[float, float]:
        """Estimate USD price from the output distribution."""
        # Remove noise and normalize
        self._clean_distribution()
        
        # Find best stencil fit
        best_slide, best_score = self._find_best_fit()
        
        # Calculate price from slide position
        center_p001 = 601  # 0.001 BTC position
        usd100_in_btc = self.output_bins[center_p001 + best_slide]
        price_estimate = 100 / usd100_in_btc
        
        # Get neighbor for weighted average
        neighbor_price = self._get_neighbor_price(best_slide, best_score)
        
        # Weight average
        final_price = 0.7 * price_estimate + 0.3 * neighbor_price
        
        return final_price, price_estimate
        
    def _clean_distribution(self):
        """Remove noise and normalize the distribution."""
        # Remove very small outputs (< 10k sats)
        for n in range(0, 201):
            self.bin_counts[n] = 0
            
        # Remove large outputs (> 10 BTC)
        for n in range(1601, len(self.bin_counts)):
            self.bin_counts[n] = 0
            
        # Smooth round BTC amounts
        round_btc_bins = [201, 401, 461, 496, 540, 601, 661, 696, 740, 801, 
                         861, 896, 940, 1001, 1061, 1096, 1140, 1201]
        
        for r in round_btc_bins:
            if 1 < r < len(self.bin_counts) - 1:
                self.bin_counts[r] = 0.5 * (self.bin_counts[r+1] + self.bin_counts[r-1])
                
        # Normalize
        curve_sum = sum(self.bin_counts[201:1601])
        if curve_sum > 0:
            for n in range(201, 1601):
                self.bin_counts[n] /= curve_sum
                if self.bin_counts[n] > 0.008:
                    self.bin_counts[n] = 0.008
                    
    def _find_best_fit(self) -> Tuple[int, float]:
        """Find the best stencil fit position."""
        best_slide = 0
        best_score = 0
        
        min_slide = -141  # $500k
        max_slide = 201   # $5k
        
        for slide in range(min_slide, max_slide):
            score = self._calculate_slide_score(slide)
            if score > best_score:
                best_score = score
                best_slide = slide
                
        return best_slide, best_score
        
    def _calculate_slide_score(self, slide: int) -> float:
        """Calculate score for a given slide position."""
        center = 601 - int((len(self.spike_stencil) + 1) / 2)
        left = center + slide
        right = left + len(self.spike_stencil)
        
        if left < 0 or right >= len(self.bin_counts):
            return 0
            
        shifted_curve = self.bin_counts[left:right]
        
        # Spike score
        spike_score = sum(shifted_curve[i] * self.spike_stencil[i] 
                         for i in range(len(self.spike_stencil)))
        
        # Smooth score (only for certain ranges)
        smooth_score = 0
        if slide < 150:
            smooth_score = sum(shifted_curve[i] * self.smooth_stencil[i] 
                             for i in range(len(self.smooth_stencil)))
            
        return spike_score + 0.65 * smooth_score
        
    def _get_neighbor_price(self, best_slide: int, best_score: float) -> float:
        """Get weighted neighbor price for averaging."""
        # Calculate neighbor scores
        up_score = self._calculate_slide_score(best_slide + 1)
        down_score = self._calculate_slide_score(best_slide - 1)
        
        # Choose best neighbor
        if up_score > down_score:
            neighbor_slide = best_slide + 1
        else:
            neighbor_slide = best_slide - 1
            
        # Calculate neighbor price
        center_p001 = 601
        usd100_in_btc = self.output_bins[center_p001 + neighbor_slide]
        return 100 / usd100_in_btc
