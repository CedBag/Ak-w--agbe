document.addEventListener('DOMContentLoaded', function () {
    // Gestion du graphique des dépenses sur dashboard.html
    if (document.getElementById('expensesChart')) {
        var ctx = document.getElementById('expensesChart');
        if (ctx && Array.isArray(categoriesLabels) && Array.isArray(categoriesAmounts) && categoriesLabels.length > 0) {
            var chart = new Chart(ctx.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: categoriesLabels,
                    datasets: [{
                        data: categoriesAmounts,
                        backgroundColor: [
                            "#2A323B", "#F38020", "#445160", "#F6A055", "#64748B", "#F9C08A"
                        ],
                        borderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                font: {
                                    size: 14
                                }
                            }
                        }
                    }
                }
            });
        } else {
            var message = document.createElement('p');
            message.textContent = 'Aucune dépense à afficher pour le moment.';
            document.body.appendChild(message);
        }
    }

    // Gestion du graphique des revenus sur dashboard.html
    if (document.getElementById('revenuesChart')) {
        var ctxRevenues = document.getElementById('revenuesChart');
        if (ctxRevenues && Array.isArray(revenueLabels) && Array.isArray(revenueAmounts) && revenueLabels.length > 0) {
            var revenuesChart = new Chart(ctxRevenues.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: revenueLabels,
                    datasets: [{
                        data: revenueAmounts,
                        backgroundColor: [
                            "#F38020", "#2A323B", "#F6A055", "#445160", "#F9C08A", "#64748B"
                        ],
                        borderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                font: {
                                    size: 14
                                }
                            }
                        }
                    }
                }
            });
        } else {
            var message = document.createElement('p');
            message.textContent = 'Aucun revenu à afficher pour le moment.';
            document.body.appendChild(message);
        }
    }

    // Gestion du graphique et des filtres sur view_expenses.html
    if (document.getElementById('allExpensesChart')) {
        const chartCanvas = document.getElementById('allExpensesChart');
        const yearFilter = document.getElementById('year-filter');
        const monthFilter = document.getElementById('month-filter');
        const dayFilter = document.getElementById('day-filter');
        const expensesTableBody = document.getElementById('expenses-table-body');

        let chart = null;

        // Vérifier que allExpenses est une liste
        if (!Array.isArray(allExpenses)) {
            allExpenses = [];
        }

        // Fonction pour regrouper les données par catégorie
        function groupByCategory(expenses) {
            const grouped = {};
            expenses.forEach(expense => {
                const category = expense[1]; // Catégorie
                const amount = parseFloat(expense[0]) || 0; // Montant
                if (!grouped[category]) {
                    grouped[category] = 0;
                }
                grouped[category] += amount;
            });
            return grouped;
        }

        // Fonction pour mettre à jour le graphique et le tableau
        function updateChartAndTable() {
            const year = yearFilter.value;
            const month = monthFilter.value;
            const day = dayFilter.value;

            // Filtrer les dépenses
            let filteredExpenses = allExpenses.filter(expense => {
                if (!expense[2]) return false; // Vérifier si la date existe
                const date = new Date(expense[2]); // Date au format YYYY-MM-DD
                if (isNaN(date.getTime())) return false; // Vérifier si la date est valide
                const expenseYear = date.getFullYear().toString();
                const expenseMonth = (date.getMonth() + 1).toString().padStart(2, '0');
                const expenseDay = date.getDate().toString().padStart(2, '0');

                return (
                    (!year || expenseYear === year) &&
                    (!month || expenseMonth === month) &&
                    (!day || expenseDay === day)
                );
            });

            // Regrouper par catégorie pour le graphique
            const groupedData = groupByCategory(filteredExpenses);
            const labels = Object.keys(groupedData);
            const amounts = Object.values(groupedData);

            // Mettre à jour le tableau
            expensesTableBody.innerHTML = '';
            filteredExpenses.forEach(expense => {
                if (expense && expense.length === 4) { // Vérifier la structure
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${expense[0] || 0}</td>
                        <td>${expense[1] || ''}</td>
                        <td>${expense[2] || ''}</td>
                        <td>${expense[3] || ''}</td>
                    `;
                    expensesTableBody.appendChild(row);
                }
            });

            // Mettre à jour le graphique
            if (chart) {
                chart.destroy();
            }

            if (labels.length > 0) {
                chart = new Chart(chartCanvas, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Dépenses par Catégorie (XOF)',
                            data: amounts,
                            backgroundColor: [
                                "#2A323B", "#F38020", "#445160", "#F6A055", "#64748B", "#F9C08A"
                            ],
                            borderColor: '#fff',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Montant (XOF)'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Catégorie'
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function (context) {
                                        return context.dataset.label + ': ' + context.raw + ' XOF';
                                    }
                                }
                            }
                        }
                    }
                });
            } else {
                chartCanvas.style.display = 'none'; // Masquer le canvas si pas de données
                const message = document.createElement('p');
                message.textContent = 'Aucune dépense à afficher pour les filtres sélectionnés.';
                chartCanvas.parentNode.insertBefore(message, chartCanvas);
            }
        }

        // Initialiser le graphique et le tableau
        updateChartAndTable();

        // Ajouter des écouteurs d'événements pour les filtres
        [yearFilter, monthFilter, dayFilter].forEach(filter => {
            if (filter) filter.addEventListener('change', updateChartAndTable);
        });
    }

    // Gestion du graphique et des filtres sur view_revenues.html
    if (document.getElementById('allRevenuesChart')) {
        const chartCanvas = document.getElementById('allRevenuesChart');
        const yearFilter = document.getElementById('year-filter');
        const monthFilter = document.getElementById('month-filter');
        const dayFilter = document.getElementById('day-filter');
        const revenuesTableBody = document.getElementById('revenues-table-body');

        let chart = null;

        // Vérifier que allRevenues est une liste
        if (!Array.isArray(allRevenues)) {
            allRevenues = [];
        }

        // Fonction pour regrouper les données par catégorie
        function groupByCategory(revenues) {
            const grouped = {};
            revenues.forEach(revenue => {
                const category = revenue[1]; // Catégorie
                const amount = parseFloat(revenue[0]) || 0; // Montant
                if (!grouped[category]) {
                    grouped[category] = 0;
                }
                grouped[category] += amount;
            });
            return grouped;
        }

        // Fonction pour mettre à jour le graphique et le tableau
        function updateChartAndTable() {
            const year = yearFilter.value;
            const month = monthFilter.value;
            const day = dayFilter.value;

            // Filtrer les revenus
            let filteredRevenues = allRevenues.filter(revenue => {
                if (!revenue[2]) return false; // Vérifier si la date existe
                const date = new Date(revenue[2]); // Date au format YYYY-MM-DD
                if (isNaN(date.getTime())) return false; // Vérifier si la date est valide
                const revenueYear = date.getFullYear().toString();
                const revenueMonth = (date.getMonth() + 1).toString().padStart(2, '0');
                const revenueDay = date.getDate().toString().padStart(2, '0');

                return (
                    (!year || revenueYear === year) &&
                    (!month || revenueMonth === month) &&
                    (!day || revenueDay === day)
                );
            });

            // Regrouper par catégorie pour le graphique
            const groupedData = groupByCategory(filteredRevenues);
            const labels = Object.keys(groupedData);
            const amounts = Object.values(groupedData);

            // Mettre à jour le tableau
            revenuesTableBody.innerHTML = '';
            filteredRevenues.forEach(revenue => {
                if (revenue && revenue.length === 4) { // Vérifier la structure
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${revenue[0] || 0}</td>
                        <td>${revenue[1] || ''}</td>
                        <td>${revenue[2] || ''}</td>
                        <td>${revenue[3] || ''}</td>
                    `;
                    revenuesTableBody.appendChild(row);
                }
            });

            // Mettre à jour le graphique
            if (chart) {
                chart.destroy();
            }

            if (labels.length > 0) {
                chart = new Chart(chartCanvas, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Revenus par Catégorie (XOF)',
                            data: amounts,
                            backgroundColor: [
                                "#F38020", "#2A323B", "#F6A055", "#445160", "#F9C08A", "#64748B"
                            ],
                            borderColor: '#fff',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Montant (XOF)'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Catégorie'
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function (context) {
                                        return context.dataset.label + ': ' + context.raw + ' XOF';
                                    }
                                }
                            }
                        }
                    }
                });
            } else {
                chartCanvas.style.display = 'none'; // Masquer le canvas si pas de données
                const message = document.createElement('p');
                message.textContent = 'Aucun revenu à afficher pour les filtres sélectionnés.';
                chartCanvas.parentNode.insertBefore(message, chartCanvas);
            }
        }

        // Initialiser le graphique et le tableau
        updateChartAndTable();

        // Ajouter des écouteurs d'événements pour les filtres
        [yearFilter, monthFilter, dayFilter].forEach(filter => {
            if (filter) filter.addEventListener('change', updateChartAndTable);
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const passwordInput = document.getElementById("password");
    const rules = document.querySelectorAll(".password-rules li");

    if (passwordInput) {
        passwordInput.addEventListener("input", function () {
            const value = passwordInput.value;
            const conditions = [
                /.{8,}/.test(value),         // min 8 caractères
                /[A-Z]/.test(value),         // majuscule
                /[a-z]/.test(value),         // minuscule
                /\d/.test(value),            // chiffre
                /[^A-Za-z0-9]/.test(value),  // caractère spécial
            ];

            rules.forEach((rule, index) => {
                rule.style.color = conditions[index] ? "green" : "gray";
            });
        });
    }

    const codeBtn = document.querySelector("button[onclick='generateCode()']");
    if (codeBtn) {
        codeBtn.addEventListener("click", function () {
            console.log("[SIMULATION] Code envoyé (visible uniquement ici en local).");
            document.getElementById("code-message").style.display = "inline";
        });
    }
});
function generateCode() {
    fetch('/generate-code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            console.log("[DEBUG] Code envoyé :", data.message);
            document.getElementById("code-message").style.display = "inline";
        })
        .catch(error => {
            console.error("Erreur lors de la génération du code :", error);
        });
}