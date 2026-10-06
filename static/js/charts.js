/* AUTHENTIX Chart.js AI Intelligence Analytics Renderer */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof Chart === 'undefined') return;

    // Set Chart.js global dark theme defaults
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.08)';
    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

    // Read chart data embedded in window.aiChartData if available
    const data = window.aiChartData || null;
    if (!data) return;

    // 1. Daily Verification Count Line Chart
    const dailyCanvas = document.getElementById('dailyChart');
    if (dailyCanvas) {
        new Chart(dailyCanvas, {
            type: 'line',
            data: {
                labels: data.daily_labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Verifications',
                    data: data.daily_counts || [0, 0, 0, 0, 0, 0, 0],
                    borderColor: '#00F2FE',
                    backgroundColor: 'rgba(0, 242, 254, 0.12)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: '#00F2FE',
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 2. Successful vs Failed Verification Doughnut Chart
    const statusCanvas = document.getElementById('statusChart');
    if (statusCanvas) {
        const statusData = data.verification_status || { success: 0, failed: 0, suspicious: 0 };
        new Chart(statusCanvas, {
            type: 'doughnut',
            data: {
                labels: ['Genuine Verified', 'Failed / Counterfeit', 'Suspicious Spikes'],
                datasets: [{
                    data: [statusData.success, statusData.failed, statusData.suspicious],
                    backgroundColor: ['#10B981', '#EF4444', '#F59E0B'],
                    borderWidth: 0,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 14, padding: 16 } }
                },
                cutout: '70%'
            }
        });
    }

    // 3. Risk Distribution Bar Chart
    const riskDistCanvas = document.getElementById('riskDistChart');
    if (riskDistCanvas) {
        const dist = data.risk_distribution || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
        new Chart(riskDistCanvas, {
            type: 'bar',
            data: {
                labels: ['LOW (0-30)', 'MEDIUM (31-60)', 'HIGH (61-80)', 'CRITICAL (81-100)'],
                datasets: [{
                    label: 'Products Count',
                    data: [dist.LOW, dist.MEDIUM, dist.HIGH, dist.CRITICAL],
                    backgroundColor: ['#10B981', '#F59E0B', '#EF4444', '#E11D48'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 4. Most Frequently Verified Products Horizontal Bar
    const topProdCanvas = document.getElementById('topProdChart');
    if (topProdCanvas && window.aiTopProducts) {
        const topProds = window.aiTopProducts;
        new Chart(topProdCanvas, {
            type: 'bar',
            data: {
                labels: topProds.map(p => p.product_name.replace('[DEMO] ', '')),
                datasets: [{
                    label: 'Scan Count',
                    data: topProds.map(p => p.total_attempts),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    y: { grid: { display: false } }
                }
            }
        });
    }
});
