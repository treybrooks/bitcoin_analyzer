from typing import List, Tuple, Dict
from math import log10

def build_smooth_stencil():
        """Initialize smooth and spike stencils for price detection."""
        # Smooth stencil - Gaussian-like
        num_elements = 803
        mean = 411
        std_dev = 201
        
        smooth_stencil = []
        for x in range(num_elements):
            exp_part = -((x - mean) ** 2) / (2 * (std_dev ** 2))
            smooth_stencil.append( (.00150 * 2.718281828459045 ** exp_part) + (.0000005 * x) )
        
        return smooth_stencil
            
def build_spike_stencil():
    # Spike stencil - USD round amounts
    spike_stencil = []
    for _ in range(803):
        spike_stencil.append(0.0)
    
    # Popular USD amounts and their weights
    spike_stencil[40] = 0.001300198324984352  # $1
    spike_stencil[141]= 0.001676746949820743  # $5
    spike_stencil[201]= 0.003468805546942046  # $10
    spike_stencil[202]= 0.001991977522512513  # 
    spike_stencil[236]= 0.001905066647961839  # $15
    spike_stencil[261]= 0.003341772718156079  # $20
    spike_stencil[262]= 0.002588902624584287  # 
    spike_stencil[296]= 0.002577893841190244  # $30
    spike_stencil[297]= 0.002733728814200412  # 
    spike_stencil[340]= 0.003076117748975647  # $50
    spike_stencil[341]= 0.005613067550103145  # 
    spike_stencil[342]= 0.003088253178535568  # 
    spike_stencil[400]= 0.002918457489366139  # $100
    spike_stencil[401]= 0.006174500465286022  # 
    spike_stencil[402]= 0.004417068070043504  # 
    spike_stencil[403]= 0.002628663628020371  # 
    spike_stencil[436]= 0.002858828161543839  # $150
    spike_stencil[461]= 0.004097463611984264  # $200
    spike_stencil[462]= 0.003345917406120509  # 
    spike_stencil[496]= 0.002521467726855856  # $300
    spike_stencil[497]= 0.002784125730361008  # 
    spike_stencil[541]= 0.003792850444811335  # $500
    spike_stencil[601]= 0.003688240815848247  # $1000
    spike_stencil[602]= 0.002392400117402263  # 
    spike_stencil[636]= 0.001280993059008106  # $1500
    spike_stencil[661]= 0.001654665137536031  # $2000
    spike_stencil[662]= 0.001395501347054946  # 
    spike_stencil[741]= 0.001154279140906312  # $5000
    spike_stencil[801]= 0.000832244504868709  # $10000
    
    return spike_stencil
        
class PriceEstimator:
    """Estimate Bitcoin price from transaction output distributions."""
    
    def __init__(self):
        # Bell curve parameters
        self.first_bin_value = -6
        self.last_bin_value = 6
        self.bins_per_10x = 200
        
        # look for prices between 5k and 500k
        self.min_slide = -141  # $500k
        self.max_slide = 201   # $5k
        
        # Initialize bins and stencils
        self._init_bins()
        self.spike_stencil = build_spike_stencil()
        self.smooth_stencil = build_smooth_stencil()
        
        # 601 is where 0.001 btc is in the output bell curve
        self.center = 601
        self.left   = self.center - int((len(self.spike_stencil) +1)/2)
        self.right  = self.center + int((len(self.spike_stencil) +1)/2)
        
    def _init_bins(self):
        """Initialize output bell curve bins."""
        self.output_bins = [0.0]
        
        for exponent in range(-6, 6):
            for b in range(0, 200):
                bin_value = 10 ** (exponent + b/200)
                self.output_bins.append(bin_value)
                
        self.num_bins = len(self.output_bins)
        self.bin_counts = [0.0] * self.num_bins
                    
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
        best_slide, best_score, total_score = self._find_best_fit()
        
        # Calculate price from slide position
        usd100_in_btc = self.output_bins[self.center + best_slide]
        rough_price_estimate = 100 / usd100_in_btc
        
        # Get neighbor for weighted average
        neighbor_price, neighbor_score = self._get_neighbor_price(best_slide, best_score)
        
        # Weight average
        #weight average the two usd price estimates
        avg_score = total_score/len(range(self.min_slide,self.max_slide))
        a1 = best_score - avg_score
        a2 = abs(neighbor_score - avg_score)
        w1 = a1/(a1+a2)
        w2 = a2/(a1+a2)
        weighted_price_estimate = int(w1*rough_price_estimate + w2*neighbor_price)
        
        return weighted_price_estimate
        
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
        """Find the best stencil fit position.
        Score is basically fit differencial between stencle and output distribution window
        """
        best_slide = 0
        best_score = 0
        total_score = 0 
        
        for slide in range(self.min_slide, self.max_slide):
            score = self._calculate_slide_score(slide)
            if score > best_score:
                best_score = score
                best_slide = slide
                
            total_score += slide
                
        return best_slide, best_score, total_score
        
    def _calculate_slide_score(self, slide: int) -> float:
        """Calculate score for a given slide position."""
        if self.left < 0 or self.right >= len(self.bin_counts):
            return 0
            
        shifted_curve = self.bin_counts[self.left+slide:self.right+slide]
        
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
        usd100_in_btc = self.output_bins[self.center + neighbor_slide]
        neighbor_price = 100 / usd100_in_btc
        
        return neighbor_price, max([up_score, down_score])
