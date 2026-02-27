function getPrice(text) {
    const lines = text.split('\n');
    let price = "";
    const mrpLine = lines.find(l => l.toUpperCase().includes('MRP'));
    if (mrpLine) {
        // Find the first set of digits
        const match = mrpLine.match(/[\d,]+/);
        if (match) price = match[0].replace(/,/g, '');
    }
    return price;
}
console.log(getPrice("MRP: `35,000/-"));
console.log(getPrice("MRP : Rs. 51,000"));
