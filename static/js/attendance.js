/**
 * SmartAttend AI — Live Attendance Calculator & Simulation Engine
 */

document.addEventListener('DOMContentLoaded', function () {
    initLiveAttendancePreview();
    initWhatIfSimulator();
});

// Live formula calculator on single-entry form
function initLiveAttendancePreview() {
    const attendedInput = document.getElementById('inputAttended');
    const totalInput = document.getElementById('inputTotal');
    const remainingInput = document.getElementById('inputRemaining');

    if (!attendedInput || !totalInput) return;

    function updatePreview() {
        const A = parseInt(attendedInput.value, 10);
        const T = parseInt(totalInput.value, 10);
        const R = parseInt(remainingInput ? remainingInput.value : 0, 10) || 0;

        const previewBox = document.getElementById('liveCalculationPreview');
        if (!previewBox) return;

        if (isNaN(A) || isNaN(T) || T <= 0) {
            previewBox.innerHTML = '<div class="text-muted small">Enter valid attended and total counts to view live prediction.</div>';
            return;
        }

        if (A < 0 || T < 0 || R < 0) {
            previewBox.innerHTML = '<div class="text-danger small"><i class="fa-solid fa-triangle-exclamation me-1"></i> Values cannot be negative.</div>';
            return;
        }

        if (A > T) {
            previewBox.innerHTML = `<div class="text-danger small"><i class="fa-solid fa-triangle-exclamation me-1"></i> Attended (${A}) cannot exceed total conducted (${T}).</div>`;
            return;
        }

        const pct = ((A / T) * 100).toFixed(2);
        let status = 'SHORTAGE';
        let statusBadge = '<span class="badge bg-danger">Shortage (<65%)</span>';
        
        if (4 * A >= 3 * T) {
            status = 'OK';
            statusBadge = '<span class="badge bg-success">Safe (&ge;75%)</span>';
        } else if (20 * A >= 13 * T) {
            status = 'CONDONABLE';
            statusBadge = '<span class="badge bg-warning text-dark">Condonable (65%-74%)</span>';
        }

        const k = Math.max(0, 3 * T - 4 * A);
        let feasibilityBadge = '<span class="badge bg-success">On Track</span>';
        if (k > 0) {
            if (k <= R) {
                feasibilityBadge = `<span class="badge bg-info text-dark">Recovery Possible (${k} &le; ${R})</span>`;
            } else {
                feasibilityBadge = `<span class="badge bg-danger">Recovery Impossible (${k} &gt; ${R})</span>`;
            }
        }

        previewBox.innerHTML = `
            <div class="d-flex align-items-center justify-content-between p-2 rounded bg-light border">
                <div>
                    <span class="fw-bold fs-5">${pct}%</span> &bull; ${statusBadge}
                </div>
                <div class="text-end">
                    <small class="text-muted d-block">Needed to reach 75%: <strong>${k} classes</strong></small>
                    ${feasibilityBadge}
                </div>
            </div>
        `;
    }

    attendedInput.addEventListener('input', updatePreview);
    totalInput.addEventListener('input', updatePreview);
    if (remainingInput) remainingInput.addEventListener('input', updatePreview);
}

// Interactive What-If Scenario Simulator for Students
function initWhatIfSimulator() {
    const simForm = document.getElementById('whatIfSimulationForm');
    if (!simForm) return;

    simForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const recordId = document.getElementById('simRecordSelect').value;
        const additionalAttended = parseInt(document.getElementById('simAttendedAdd').value, 10) || 0;
        const additionalMissed = parseInt(document.getElementById('simMissedAdd').value, 10) || 0;
        const resultContainer = document.getElementById('simulationResult');

        if (!recordId) {
            alert('Please select a course to simulate.');
            return;
        }

        resultContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary spinner-border-sm" role="status"></div> Calculating scenario...</div>';

        fetch('/api/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                record_id: recordId,
                additional_attended: additionalAttended,
                additional_missed: additionalMissed
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultContainer.innerHTML = `<div class="alert alert-danger py-2 small mb-0">${data.error}</div>`;
                return;
            }

            const sim = data.simulation;
            let badgeClass = 'bg-danger';
            if (sim.simulated_status === 'OK') badgeClass = 'bg-success';
            else if (sim.simulated_status === 'CONDONABLE') badgeClass = 'bg-warning text-dark';

            resultContainer.innerHTML = `
                <div class="card border border-primary border-opacity-25 bg-white shadow-sm rounded-3 mt-3">
                    <div class="card-body p-3">
                        <div class="d-flex align-items-center justify-content-between mb-2">
                            <span class="badge bg-primary">${data.course_code} Simulation</span>
                            <span class="badge ${badgeClass}">${sim.simulated_status_label}</span>
                        </div>
                        <div class="row text-center my-2">
                            <div class="col-6 border-end">
                                <small class="text-muted d-block">Original</small>
                                <span class="fw-bold fs-5">${((sim.original_attended / sim.original_total) * 100).toFixed(1)}%</span>
                                <small class="text-muted d-block">${sim.original_attended} / ${sim.original_total}</small>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Simulated Result</small>
                                <span class="fw-bold fs-5 text-primary">${sim.simulated_percentage}%</span>
                                <small class="text-muted d-block">${sim.simulated_attended} / ${sim.simulated_total}</small>
                            </div>
                        </div>
                        <div class="progress progress-attendance mt-2">
                            <div class="progress-bar ${sim.simulated_status === 'OK' ? 'progress-safe' : (sim.simulated_status === 'CONDONABLE' ? 'progress-condonable' : 'progress-shortage')}" 
                                 style="width: ${sim.simulated_percentage}%;"></div>
                        </div>
                        <small class="text-muted d-block mt-2 text-center" style="font-size: 0.76rem;">
                            Attending +${sim.additional_attended} and missing +${sim.additional_missed} future classes.
                        </small>
                    </div>
                </div>
            `;
        })
        .catch(err => {
            console.error('Simulation error:', err);
            resultContainer.innerHTML = `<div class="alert alert-danger py-2 small mb-0">Failed to calculate simulation.</div>`;
        });
    });
}
