from typing import List, Tuple, Dict
from math import log10

def build_smooth_stencil():
    """Initialize smooth stencil for price detection."""
    # Smooth stencil - Gaussian-like (matches UTXOracle exactly)
    num_elements = 803
    mean = 411
    std_dev = 201
    
    smooth_stencil = []
    for x in range(num_elements):
        exp_part = -((x - mean) ** 2) / (2 * (std_dev ** 2))
        smooth_stencil.append((.00150 * 2.718281828459045 ** exp_part) + (.0000005 * x))
    
    return smooth_stencil
            
def build_spike_stencil():
    """Initialize spike stencil for USD round amounts (matches UTXOracle exactly)."""
    spike_stencil = []
    for _ in range(803):
        spike_stencil.append(0.0)
    
    # Popular USD amounts and their weights (exact values from UTXOracle)
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

def find_central_output(r2, price_min, price_max):
    """Find central price point and average deviation (matches UTXOracle exactly)."""
    # Filter prices in range and sort
    r6 = [r for r in r2 if price_min < r < price_max]
    outputs = sorted(r6)
    n = len(outputs)
    
    if n == 0:
        return 0, 0

    # Prefix sums
    prefix_sum = []
    total = 0
    for x in outputs:
        total += x
        prefix_sum.append(total)

    # Count the number of points left and right
    left_counts = list(range(n))
    right_counts = [n - i - 1 for i in left_counts]
    left_sums = [0] + prefix_sum[:-1]
    right_sums = [total - x for x in prefix_sum]

    # Find the total distance to other points
    total_dists = []
    for i in range(n):
        dist = (outputs[i] * left_counts[i] - left_sums[i]) + (right_sums[i] - outputs[i] * right_counts[i])
        total_dists.append(dist)

    # Find the most central output
    min_index, _ = min(enumerate(total_dists), key=lambda x: x[1])
    best_output = outputs[min_index]

    # Median absolute deviation
    deviations = [abs(x - best_output) for x in outputs]
    deviations.sort()
    m = len(deviations)
    if m % 2 == 0:
        mad = (deviations[m//2 - 1] + deviations[m//2]) / 2
    else:
        mad = deviations[m//2]

    return best_output, mad
        
class PriceEstimator:
    """Estimate Bitcoin price from transaction output distributions (matches UTXOracle exactly)."""
    
    def __init__(self):
        # Bell curve parameters (exact values from UTXOracle)
        self.first_bin_value = -6
        self.last_bin_value = 6
        self.range_bin_values = self.last_bin_value - self.first_bin_value
        
        # Slide range for price search (exact values from UTXOracle)
        self.min_slide = -141  # $500k
        self.max_slide = 201   # $5k
        
        # Initialize bins and stencils
        self._init_bins()
        self.spike_stencil = build_spike_stencil()
        self.smooth_stencil = build_smooth_stencil()
        
        # Center positions (exact values from UTXOracle)
        self.center_p001 = 601  # where 0.001 btc is in the output bell curve
        self.left_p001 = self.center_p001 - int((len(self.spike_stencil) + 1) / 2)
        self.right_p001 = self.center_p001 + int((len(self.spike_stencil) + 1) / 2)
        
    def _init_bins(self):
        """Initialize output bell curve bins (matches UTXOracle exactly)."""
        # Create bins exactly as in UTXOracle
        self.output_bell_curve_bins = [0.0]  # Start with zero sats
        
        # Calculate btc amounts of 200 samples in every 10x from 100 sats (1e-6 btc) to 100k (1e5) btc
        for exponent in range(-6, 6):  # python range uses 'less than' for the big number
            for b in range(0, 200):
                bin_value = 10 ** (exponent + b/200)
                self.output_bell_curve_bins.append(bin_value)
                
        # Create count array
        self.number_of_bins = len(self.output_bell_curve_bins)
        self.output_bell_curve_bin_counts = [0.0] * self.number_of_bins
                    
    def add_output(self, amount_btc: float):
        """Add a transaction output to the distribution (matches UTXOracle exactly)."""
        if amount_btc <= 0:
            return
            
        # Exact logic from UTXOracle Part 6
        amount_log = log10(amount_btc)
        percent_in_range = (amount_log - self.first_bin_value) / self.range_bin_values
        bin_number_est = int(percent_in_range * self.number_of_bins)
        
        # Ensure we don't go out of bounds
        if bin_number_est >= self.number_of_bins - 1:
            bin_number_est = self.number_of_bins - 2
        elif bin_number_est < 0:
            bin_number_est = 0
            
        # Find correct bin
        while (bin_number_est < self.number_of_bins - 1 and 
               self.output_bell_curve_bins[bin_number_est] <= amount_btc):
            bin_number_est += 1
        bin_number = bin_number_est - 1
        
        if 0 <= bin_number < self.number_of_bins:
            self.output_bell_curve_bin_counts[bin_number] += 1.0
            
    def estimate_price(self) -> float:
        """Estimate USD price from the output distribution (matches UTXOracle exactly)."""
        # Clean and normalize distribution first
        self._clean_distribution()
        
        # Find best stencil fit (Part 8)
        best_slide, best_slide_score, total_score = self._find_best_fit()
        
        # Calculate rough price estimate (exact UTXOracle logic)
        usd100_in_btc_best = self.output_bell_curve_bins[self.center_p001 + best_slide]
        btc_in_usd_best = 100 / usd100_in_btc_best
        
        # Get neighbor prices for weighted average
        neighbor_up_score = self._calculate_slide_score(best_slide + 1)
        neighbor_down_score = self._calculate_slide_score(best_slide - 1)
        
        #get best neighbor
        best_neighbor = +1
        neighbor_score = neighbor_up_score
        if neighbor_down_score > neighbor_up_score:
            best_neighbor = -1
            neighbor_score = neighbor_down_score
            
        # Get best neighbor usd price
        usd100_in_btc_2nd = self.output_bell_curve_bins[self.center_p001 + best_slide + best_neighbor]
        btc_in_usd_2nd = 100 / usd100_in_btc_2nd
        
        # Weighted average the two usd price estimates (exact logic from UTXOracle)
        num_slides = len(range(self.min_slide, self.max_slide))
        avg_score = total_score / num_slides
        a1 = best_slide_score - avg_score
        a2 = abs(neighbor_score - avg_score)
        w1 = a1 / (a1 + a2)
        w2 = a2 / (a1 + a2)
        rough_price_estimate = int(w1 * btc_in_usd_best + w2 * btc_in_usd_2nd)
        
        return rough_price_estimate
        
    def _clean_distribution(self):
        """Remove noise and normalize the distribution (matches UTXOracle Part 9 exactly)."""
        # Remove outputs below 10k sat (increased from 1k sat in v6)
        for n in range(0, 201):
            self.output_bell_curve_bin_counts[n] = 0

        # Remove outputs above ten btc
        for n in range(1601, len(self.output_bell_curve_bin_counts)):
            self.output_bell_curve_bin_counts[n] = 0

        # Create a list of round btc bin numbers (exact values from UTXOracle)
        round_btc_bins = [
            201,   # 1k sats
            401,   # 10k 
            461,   # 20k
            496,   # 30k
            540,   # 50k
            601,   # 100k 
            661,   # 200k
            696,   # 300k
            740,   # 500k
            801,   # 0.01 btc
            861,   # 0.02
            896,   # 0.03
            940,   # 0.04
            1001,  # 0.1 
            1061,  # 0.2
            1096,  # 0.3
            1140,  # 0.5
            1201   # 1 btc
        ]

        # Smooth over the round btc amounts
        for r in round_btc_bins:
            if 0 < r < len(self.output_bell_curve_bin_counts) - 1:
                amount_above = self.output_bell_curve_bin_counts[r + 1]
                amount_below = self.output_bell_curve_bin_counts[r - 1]
                self.output_bell_curve_bin_counts[r] = 0.5 * (amount_above + amount_below)

        # Get the sum of the curve
        curve_sum = 0.0
        for n in range(201, 1601):
            curve_sum += self.output_bell_curve_bin_counts[n]

        # Normalize the curve by dividing by its sum and removing extreme values
        if curve_sum > 0:
            for n in range(201, 1601):
                self.output_bell_curve_bin_counts[n] /= curve_sum
                
                # Remove extremes (0.008 chosen by historical testing)
                if self.output_bell_curve_bin_counts[n] > 0.008:
                    self.output_bell_curve_bin_counts[n] = 0.008
        else:
            # If no valid data, set a small uniform distribution to prevent errors
            for n in range(201, 1601):
                self.output_bell_curve_bin_counts[n] = 1e-10
                    
    def _find_best_fit(self) -> Tuple[int, float, float]:
        """Find the best stencil fit position."""
        best_slide = 0
        best_slide_score = 0
        total_score = 0
        
        # Weighting of the smooth and spike slide scores
        smooth_weight = 0.65
        
        for slide in range(self.min_slide, self.max_slide):
            # Shift the bell curve by the slide
            shifted_curve = self.output_bell_curve_bin_counts[self.left_p001 + slide:self.right_p001 + slide]
                
            # Score the smooth slide by multiplying the curve by the stencil
            slide_score_smooth = 0.0
            for n in range(len(self.smooth_stencil)):
                slide_score_smooth += shifted_curve[n] * self.smooth_stencil[n]
            
            # Score the spiky slide by multiplying the curve by the stencil
            slide_score = 0.0
            for n in range(len(self.spike_stencil)):
                slide_score += shifted_curve[n] * self.spike_stencil[n]
            
            # Add the spike and smooth slide scores, neglect smooth slide over wrong regions
            if slide < 150:
                slide_score = slide_score + slide_score_smooth * smooth_weight
                
            # See if this score is the best so far
            if slide_score > best_slide_score:
                best_slide_score = slide_score
                best_slide = slide
            
            # Increment the total score
            total_score += slide_score
                
        return best_slide, best_slide_score, total_score
        
    def _calculate_slide_score(self, slide: int) -> float:
        """Calculate score for a given slide position (matches UTXOracle logic)."""
        neighbor = self.output_bell_curve_bin_counts[self.left_p001+slide:self.right_p001+slide]
        neighbor_score = 0.0
        for n in range(0,len(self.spike_stencil)):
            neighbor_score += neighbor[n]*self.spike_stencil[n]
        return neighbor_score
            
    def _refine_with_central_output(self, rough_price_estimate: float, output_prices: List[float]) -> float:
        """Refine price estimate using central output analysis (matches UTXOracle Parts 9-10)."""
        # Use a tight pct range to find the first central price
        pct_range_tight = 0.05
        price_up = rough_price_estimate + pct_range_tight * rough_price_estimate 
        price_dn = rough_price_estimate - pct_range_tight * rough_price_estimate
        central_price, av_dev = find_central_output(output_prices, price_dn, price_up)

        # Iteratively re-center the bounds and find a new center price until convergence
        avs = set()
        avs.add(central_price)
        while central_price not in avs:
            avs.add(central_price)
            price_up = central_price + pct_range_tight * central_price 
            price_dn = central_price - pct_range_tight * central_price
            central_price, av_dev = find_central_output(output_prices, price_dn, price_up)

        return central_price