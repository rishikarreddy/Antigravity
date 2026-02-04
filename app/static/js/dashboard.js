// Dashboard Real-time Updates

document.addEventListener('DOMContentLoaded', function () {

    // Only run if we are on the dashboard (elements exist)
    if (!document.getElementById('confidence-val')) return;

    function fetchStats() {
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                updateConfidenceMeter(data.recognition);
                updateUnknownFaces(data.unknown_faces);
                updateSessionInfo(data.session);
                updateSystemHealth(data.health);
                updateEngagement(data.summary);
            })
            .catch(err => console.error('Error fetching stats:', err));
    }

    function updateConfidenceMeter(data) {
        document.getElementById('confidence-val').innerText = data.confidence + '%';
        document.getElementById('rec-time').innerText = data.time + 's';

        const meter = document.getElementById('confidence-meter-bar');
        meter.style.width = data.confidence + '%';

        if (data.is_spoof) {
            document.getElementById('spoof-indicator').classList.remove('d-none');
        } else {
            document.getElementById('spoof-indicator').classList.add('d-none');
        }
    }

    function updateUnknownFaces(data) {
        document.getElementById('unknown-count').innerText = data.count;
        if (data.last_seen) {
            document.getElementById('unknown-last-seen').innerText = 'Last at ' + data.last_seen;
        }
    }

    function updateSessionInfo(data) {
        // Logic for timer
        // Simplified: just show a static or mock countdown if data comes in
    }

    function updateSystemHealth(data) {
        // Update badges
        updateStatusBadge('cam-status', data.camera);
        updateStatusBadge('model-status', data.model);
        updateStatusBadge('db-status', data.database);
    }

    function updateStatusBadge(id, status) {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerText = status;
        if (status === 'Active' || status === 'Connected' || status === 'Loaded' || status === 'Synced' || status === 'Running') {
            el.className = 'badge bg-success';
        } else {
            el.className = 'badge bg-danger';
        }
    }

    function updateEngagement(data) {
        if (document.getElementById('total-classes'))
            document.getElementById('total-classes').innerText = data.total_classes;
        if (document.getElementById('avg-attendance'))
            document.getElementById('avg-attendance').innerText = data.attendance_percent + '%';
    }

    // Initial fetch
    fetchStats();
    // Poll every 5 seconds
    setInterval(fetchStats, 5000);
});

// Student Attendance Graph
if (document.getElementById('attendanceChart')) {
    fetch('/api/student/attendance_history')
        .then(res => res.json())
        .then(data => {
            const ctx = document.getElementById('attendanceChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Attendance Status',
                        data: data.data,
                        borderColor: '#4e73df',
                        backgroundColor: 'rgba(78, 115, 223, 0.05)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1.2,
                            ticks: {
                                callback: function (value) {
                                    if (value == 1) return 'Present';
                                    if (value == 0.5) return 'Late';
                                    if (value == 0) return 'Absent';
                                    return '';
                                }
                            }
                        }
                    }
                }
            });
        });
}
