// admin.js — NeuralChat Admin Dashboard

document.addEventListener('DOMContentLoaded', () => {

    // Elements
    const totalChatsEl   = document.getElementById('totalChats');
    const topIntentValEl = document.getElementById('topIntentVal');
    const todayCountEl   = document.getElementById('todayCount');
    const totalIntentsEl = document.getElementById('totalIntents');
    const lastRefreshEl  = document.getElementById('lastRefresh');
    const convoTableBody = document.getElementById('convoTableBody');
    const tableSearch    = document.getElementById('tableSearch');

    // Chart instances
    let barChart, doughnutChart, lineChart;

    const colors = [
        '#6c5ce7','#a29bfe','#00cec9','#fdcb6e','#e17055',
        '#0984e3','#00b894','#e84393','#6366f1','#f97316',
        '#8b5cf6','#ef4444'
    ];

    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            const total       = data.total_conversations || 0;
            const intentDist  = data.intent_distribution || [];
            const dailyVol    = data.daily_volume || [];
            const recent      = data.recent_conversations || [];

            // Update stat cards
            if (totalChatsEl) totalChatsEl.textContent = total;

            // Top intent
            if (topIntentValEl) {
                if (intentDist.length > 0) {
                    topIntentValEl.textContent = intentDist[0].intent || 'N/A';
                } else {
                    topIntentValEl.textContent = 'N/A';
                }
            }

            // Today count (last entry in daily volume)
            if (todayCountEl) {
                const todayData = dailyVol.length > 0 ? dailyVol[dailyVol.length - 1].count : 0;
                todayCountEl.textContent = todayData;
            }

            // Total categories
            if (totalIntentsEl) totalIntentsEl.textContent = intentDist.length;

            // Last refresh time
            const now = new Date();
            if (lastRefreshEl) lastRefreshEl.textContent = now.toLocaleTimeString();

            // Prepare chart data from arrays
            const intentLabels = intentDist.map(d => d.intent);
            const intentData   = intentDist.map(d => d.count);

            const dailyLabels = dailyVol.map(d => d.date);
            const dailyData   = dailyVol.map(d => d.count);

            renderBarChart(intentLabels, intentData);
            renderDoughnutChart(intentLabels, intentData);
            renderLineChart(dailyLabels, dailyData);
            renderTable(recent);

        } catch (err) {
            console.error("Failed to load admin stats:", err);
        }
    }

    function renderBarChart(labels, dataArr) {
        const ctx = document.getElementById('intentBarChart');
        if (!ctx) return;

        if (barChart) {
            barChart.data.labels = labels;
            barChart.data.datasets[0].data = dataArr;
            barChart.update();
            return;
        }

        barChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Requests',
                    data: dataArr,
                    backgroundColor: colors.slice(0, labels.length),
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8888a0' } },
                    x: { grid: { display: false }, ticks: { color: '#8888a0' } }
                }
            }
        });
    }

    function renderDoughnutChart(labels, dataArr) {
        const ctx = document.getElementById('intentDoughnut');
        if (!ctx) return;

        if (doughnutChart) {
            doughnutChart.data.labels = labels;
            doughnutChart.data.datasets[0].data = dataArr;
            doughnutChart.update();
            return;
        }

        doughnutChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: dataArr,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: { position: 'right', labels: { color: '#f0f0f5', padding: 12, font: { size: 11 } } }
                }
            }
        });
    }

    function renderLineChart(labels, dataArr) {
        const ctx = document.getElementById('dailyLineChart');
        if (!ctx) return;

        if (lineChart) {
            lineChart.data.labels = labels;
            lineChart.data.datasets[0].data = dataArr;
            lineChart.update();
            return;
        }

        lineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Daily Chats',
                    data: dataArr,
                    borderColor: '#6c5ce7',
                    backgroundColor: 'rgba(108, 92, 231, 0.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6c5ce7',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8888a0' } },
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8888a0' } }
                }
            }
        });
    }

    function renderTable(rows) {
        if (!convoTableBody) return;
        convoTableBody.innerHTML = '';

        if (rows.length === 0) {
            convoTableBody.innerHTML = '<tr><td colspan="6" class="loading-row">No conversations yet. Start chatting!</td></tr>';
            return;
        }

        rows.forEach((r, i) => {
            const tr = document.createElement('tr');
            const conf = r.confidence != null ? r.confidence + '%' : '—';
            const intentClass = r.detected_intent === 'gemini' ? 'style="background:rgba(108,92,231,0.2);color:#a29bfe"' : '';
            tr.innerHTML = `
                <td>${i + 1}</td>
                <td>${(r.user_message || '—').substring(0, 60)}${(r.user_message || '').length > 60 ? '...' : ''}</td>
                <td style="color:var(--text-muted)">${(r.bot_response || '—').substring(0, 80)}${(r.bot_response || '').length > 80 ? '...' : ''}</td>
                <td><span class="intent-chip" ${intentClass}>${r.detected_intent || '—'}</span></td>
                <td>${conf}</td>
                <td style="white-space:nowrap">${r.timestamp || '—'}</td>
            `;
            convoTableBody.appendChild(tr);
        });
    }

    window.filterTable = function() {
        if (!tableSearch || !convoTableBody) return;
        const val = tableSearch.value.toLowerCase();
        const rows = convoTableBody.querySelectorAll('tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(val) ? '' : 'none';
        });
    };

    // Auto-refresh
    window.loadStats = loadStats;
    loadStats();
    setInterval(loadStats, 60000);
});
