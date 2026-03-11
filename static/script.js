// -----------------------------
// AI Prediction Form Handling
// -----------------------------
const form = document.getElementById("expenseForm");
const resultDiv = document.getElementById("resultDiv");

if (form && resultDiv) {
    form.addEventListener("submit", function(event){
        event.preventDefault();

        resultDiv.style.display = "block";
        resultDiv.innerHTML = "<p>Analyzing your spending with AI...</p>";

        const formData = new FormData(form);

        fetch("/predict", {
            method: "POST",
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const predictionDiv = doc.querySelector(".result");

            if(predictionDiv){
                resultDiv.innerHTML = predictionDiv.innerHTML;
            }
        })
        .catch(error => {
            console.error("Error:", error);
            resultDiv.innerHTML = "<p>Error analyzing your spending. Try again.</p>";
        });
    });
}

// -----------------------------
// Dynamic Dashboard Chart
// -----------------------------
async function loadChart() {
    const chartElement = document.getElementById("categoryChart");
    if (!chartElement) return;

    try {
        const response = await fetch("/category_data");
        const result = await response.json();

        const data = [{
            type: "pie",
            labels: result.categories,
            values: result.amounts,
            textinfo: "label+percent",
            insidetextorientation: "radial"
        }];

        const layout = {
            title: "Spending by Category"
        };

        Plotly.newPlot("categoryChart", data, layout);

    } catch (error) {
        console.error("Chart load error:", error);
    }
}

// -----------------------------
// Auto Load Chart if Dashboard
// -----------------------------
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("categoryChart")) {
        loadChart();
        setInterval(loadChart, 5000);
    }
});
