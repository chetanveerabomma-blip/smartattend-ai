/**
 * SmartAttend AI — Dashboard Charts & Analytics Engine
 * Connects Chart.js with verified database metrics from /api/dashboard/charts
 */

document.addEventListener('DOMContentLoaded', function () {
    fetchDashboardCharts();
});

function fetchDashboardCharts() {
    fetch('/api/dashboard/charts')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            renderStatusDoughnut(data.status_doughnut);
            renderCourseBar(data.course_bar);
            renderTrendLine(data.trend_line);
            renderLowestStudentsBar(data.lowest_bar);
        })
        .catch(error => {
            console.error('Error fetching dashboard chart data:', error);
        });
}

// 1. Status Distribution Doughnut Chart
function renderStatusDoughnut(data) {
    const ctx = document.getElementById('statusDoughnutChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.counts,
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                hoverBackgroundColor: ['#059669', '#d97706', '#dc2626'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: { family: 'Inter', size: 12, weight: '500' }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const val = context.raw;
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: ${val} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '72%'
        }
    });
}

// 2. Course-wise Average Attendance Bar Chart
function renderCourseBar(data) {
    const ctx = document.getElementById('courseBarChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Course Average (%)',
                    data: data.averages,
                    backgroundColor: data.averages.map(val => val >= 75 ? 'rgba(37, 99, 235, 0.85)' : (val >= 65 ? 'rgba(245, 158, 11, 0.85)' : 'rgba(239, 68, 68, 0.85)')),
                    borderRadius: 6,
                    maxBarThickness: 45
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: val => val + '%',
                        font: { family: 'Inter', size: 11 }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11, weight: '600' } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const fullName = data.full_names[context.dataIndex];
                            return `Subject: ${fullName}\nTarget Standard: 75%`;
                        }
                    }
                }
            }
        }
    });
}

// 3. Attendance Trends Line Chart
function renderTrendLine(data) {
    const ctx = document.getElementById('trendLineChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Institutional Average',
                    data: data.overall_trend,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.08)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#2563eb',
                    pointRadius: 4
                },
                {
                    label: 'Target Benchmark (75%)',
                    data: data.target_line,
                    borderColor: '#10b981',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 40,
                    max: 100,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: val => val + '%',
                        font: { family: 'Inter', size: 11 }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11 } }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: { boxWidth: 12, font: { family: 'Inter', size: 11 } }
                }
            }
        }
    });
}

// 4. Horizontal Bar Chart for Students with Lowest Attendance
function renderLowestStudentsBar(data) {
    const ctx = document.getElementById('lowestStudentsChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Attendance %',
                data: data.percentages,
                backgroundColor: data.status_colors,
                borderRadius: 4,
                maxBarThickness: 24
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: '#f1f5f9' },
                    ticks: { callback: val => val + '%' }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11, weight: '500' } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` Attendance: ${ctx.raw}% (Target: 75%)`
                    }
                }
            }
        }
    });
}
