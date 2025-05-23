from typing import List, Optional
from datetime import datetime
import os

class ChartGenerator:
    """Generate HTML/JavaScript charts for price visualization."""
    
    def generate_chart(self, estimator, block_nums: List[int], 
                      block_times: List[int], price: float,
                      is_date_mode: bool = True, 
                      target_date: Optional[datetime] = None) -> str:
        """Generate an HTML chart and return the file path."""
        
        # Prepare data for chart
        chart_data = self._prepare_chart_data(estimator, block_nums, block_times, price)
        
        # Generate HTML
        html_content = self._generate_html(chart_data, is_date_mode, target_date)
        
        # Save to file
        if is_date_mode and target_date:
            filename = f"UTXOracle_{target_date.strftime('%Y-%m-%d')}.html"
        else:
            filename = f"UTXOracle_{block_nums[0]}-{block_nums[-1]}.html"
        
        with open(filename, 'w') as f:
            f.write(html_content)
            
        return filename
    
    def _prepare_chart_data(self, estimator, block_nums, block_times, price):
        """Prepare data for chart rendering."""
        # Extract price points from estimator
        # This would include the logic for creating the visualization data
        return {
            "blocks": block_nums,
            "times": block_times,
            "price": price,
            "distribution": estimator.bin_counts,
            "bins": estimator.output_bins
        }
    
    def _generate_html(self, data, is_date_mode, target_date):
        """Generate the HTML content for the chart."""
        # This would contain the HTML template with embedded JavaScript
        # For brevity, returning a simplified version
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>UTXOracle Local</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div id="chart-container">
        <canvas id="priceChart"></canvas>
    </div>
    <script>
        // Chart rendering code here
        const data = {data};
    </script>
</body>
</html>"""