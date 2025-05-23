const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');

const width = 1000;
const height = 660;

const marginLeft = 120;
const marginRight = 90;
const marginTop = 100;
const marginBottom = 120;

const plotWidth = width - marginLeft - marginRight;
const plotHeight = height - marginTop - marginBottom;

// Data
const heights_smooth = [1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206, 1747957206];

// Add the missing data arrays that were referenced but not included
const prices = [/* your price data */];
const heights = [/* your heights data */];
const timestamps = [/* your timestamps data */];

const ymin = Math.min(...prices);
const ymax = Math.max(...prices);
const xmin = Math.min(...heights_smooth);
const xmax = Math.max(...heights_smooth);

// xticks
const xtick_positions = [897767.0, 897804.462176186, 897842.5274559145, 897879.0769838484, 897916.0];
const xtick_labels = ['897767\n00:09 UTC', '897804\n06:00 UTC', '897837\n11:23 UTC', '897870\n16:46 UTC', '897916\n23:40 UTC'];

// Scaling functions
function scaleX(t) {
    return marginLeft + (t - xmin) / (xmax - xmin) * plotWidth;
}

function scaleY(p) {
    return marginTop + (1 - (p - ymin) / (ymax - ymin)) * plotHeight;
}

// Background
ctx.fillStyle = "black";
ctx.fillRect(0, 0, width, height);

// UTXOracle Local Title
ctx.font = "bold 36px Arial";
ctx.textAlign = "center";
ctx.fillStyle = "cyan";
ctx.fillText("UTXOracle", width / 2 - 60, 40);

ctx.fillStyle = "lime";
ctx.fillText("Local", width / 2 + 95, 40);

// Plot Date and Consensus Price
ctx.font = "24px Arial";
ctx.textAlign = "right";
ctx.fillStyle = "white";
ctx.fillText("May 22, 2025 blocks from local node", width /2, 80);
ctx.textAlign = "left";
ctx.fillStyle = "lime";
ctx.fillText("UTXOracle Consensus Price $110,760 ", width/2 +10, 80);

// Draw axes
ctx.strokeStyle = "white";
ctx.lineWidth = 1;

// Y axis
ctx.beginPath();
ctx.moveTo(marginLeft, marginTop);
ctx.lineTo(marginLeft, marginTop + plotHeight);
ctx.stroke();

// X axis
ctx.beginPath();
ctx.moveTo(marginLeft, marginTop + plotHeight);
ctx.lineTo(marginLeft + plotWidth, marginTop + plotHeight);
ctx.stroke();

// Right spine
ctx.beginPath();
ctx.moveTo(marginLeft + plotWidth, marginTop);
ctx.lineTo(marginLeft + plotWidth, marginTop + plotHeight);
ctx.stroke();

// Top spine
ctx.beginPath();
ctx.moveTo(marginLeft, marginTop);
ctx.lineTo(marginLeft + plotWidth, marginTop);
ctx.stroke();

// Draw ticks and labels
ctx.fillStyle = "white";
ctx.font = "20px Arial";

// Y axis ticks
const yticks = 5;
for (let i = 0; i <= yticks; i++) {
    let p = ymin + (ymax - ymin) * i / yticks;
    let y = scaleY(p);
    ctx.beginPath();
    ctx.moveTo(marginLeft - 5, y);
    ctx.lineTo(marginLeft, y);
    ctx.stroke();
    ctx.textAlign = "right";
    ctx.fillText(Math.round(p).toLocaleString(), marginLeft - 10, y + 4);
}

// X axis ticks
ctx.textAlign = "center";
ctx.font = "16px Arial";

for (let i = 0; i < xtick_positions.length; i++) {
    let x = scaleX(xtick_positions[i]);
    ctx.beginPath();
    ctx.moveTo(x, marginTop + plotHeight);
    ctx.lineTo(x, marginTop + plotHeight + 5);
    ctx.stroke();

    // Split label into two lines
    let parts = xtick_labels[i].split("\n");
    ctx.fillText(parts[0], x, marginTop + plotHeight + 20);
    ctx.fillText(parts[1], x, marginTop + plotHeight + 40);
}

// Axis labels
ctx.fillStyle = "white";
ctx.font = "20px Arial";
ctx.textAlign = "center";
ctx.fillText("Block Height and UTC Time", marginLeft + plotWidth/2, height - 48);
ctx.save();
ctx.translate(20, marginTop + plotHeight/2);
ctx.rotate(-Math.PI / 2);
ctx.fillText("BTC Price ($)", 0, 0);
ctx.restore();

// Plot points
ctx.fillStyle = "cyan";
for (let i = 0; i < heights_smooth.length; i++) {
    let x = scaleX(heights_smooth[i]);
    let y = scaleY(prices[i]);
    ctx.fillRect(x, y, .75, .75);
}

// Annotation for average price
ctx.fillStyle = "cyan";
ctx.font = "20px Arial";
ctx.textAlign = "left";
ctx.fillText("- 110,760", marginLeft + plotWidth + 1, scaleY(110760.98333601006) +0);

// Annotate bottom chart note
ctx.font = "24px Arial";
ctx.fillStyle = "lime";
ctx.textAlign = "right";
ctx.fillText("Consensus Data:", 320, height-10);
ctx.font = "24px Arial";
ctx.fillStyle = "white";
ctx.textAlign = "left";
ctx.fillText("this plot is identical and immutable for every bitcoin node", 325, height-10);

// === MOUSEOVER INFO ===
const tooltip = document.getElementById('tooltip');

canvas.addEventListener('mousemove', function(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleXRatio = canvas.width / rect.width;
    const scaleYRatio = canvas.height / rect.height;
    const mouseX = (event.clientX - rect.left) * scaleXRatio;
    const mouseY = (event.clientY - rect.top) * scaleYRatio;

    if (mouseX >= marginLeft && mouseX <= width - marginRight &&
        mouseY >= marginTop && mouseY <= marginTop + plotHeight) {

        const fractionAcross = (mouseX - marginLeft) / plotWidth;
        let index = Math.round(fractionAcross * (heights.length - 1));
        index = Math.max(0, Math.min(index, heights.length - 1));

        const price = ymax - (mouseY - marginTop) / plotHeight * (ymax - ymin);
        const blockHeight = heights[index];
        const timestamp = timestamps[index];

        const date = new Date(timestamp * 1000);
        const hours = date.getUTCHours().toString().padStart(2, '0');
        const minutes = date.getUTCMinutes().toString().padStart(2, '0');
        const utcTime = `${hours}:${minutes} UTC`;

        tooltip.innerHTML = `
            Price: $${Math.round(price).toLocaleString()}<br>
            Block: ${blockHeight.toLocaleString()}<br>
            Time: ${utcTime}
        `;

        tooltip.style.left = (event.clientX + 5) + 'px';
        tooltip.style.top = (event.clientY + window.scrollY - 75) + 'px';
        tooltip.style.opacity = 1;
    } else {
        tooltip.style.opacity = 0;
    }
});

// Download canvas as PNG
const downloadBtn = document.getElementById('downloadBtn');
downloadBtn.addEventListener('click', function() {
    const link = document.createElement('a');
    link.download = 'UTXOracle_Local_Node_Price.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
});