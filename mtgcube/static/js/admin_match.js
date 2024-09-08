document.addEventListener('DOMContentLoaded', function() {
    function updateRoundStatus(tournamentSlug, draftSlug) {
        var url = `/admin-dashboard/${tournamentSlug}/${draftSlug}/~draft/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            var finishBtn = document.getElementById("finish-btn");
            var pairBtn = document.getElementById("pair-btn");
            var seatBtn = document.getElementById("seat-btn");
            finishBtn.disabled = true;
            pairBtn.disabled = true;
            seatBtn.disabled = true;
            if (!data.in_progress) {
                if (data.finished) {
                    pairBtn.disabled = false;
                } else {
                    finishBtn.disabled = false;
                }
                if (data.seated) {
                    pairBtn.disabled = false;
                } else {
                    seatBtn.disabled = false;
                }
            }
        })
        .catch(error => console.error('Error updating match info:', error));
    }
    function updateMatchInfo(tournamentSlug, matchId) {
        var pairingElement = document.getElementById("pairing-" + matchId);
        var pairingTextElement = document.getElementById("pairing-info-" + matchId);
        var resultElement = document.getElementById("report-result-form-" + matchId);
        var confirmElement = document.getElementById("confirm-result-form-" + matchId);
        var reportBtn = document.getElementById("report-result-btn-" + matchId);
        var confirmBtn = document.getElementById("confirm-result-btn-" + matchId);
        var url = `/admin-dashboard/${tournamentSlug}/~match/${matchId}/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            var pairingHtml = `<strong>${gettext('Table')} ${data.table}:</strong> ${data.player1} vs ${data.player2}`;
            if (data.result !== 'Pending') {
                var resultInfo = `${data.player1_wins}-${data.player2_wins}`;
                if (!data.result_confirmed) {
                    resultInfo += ` (${gettext('reported by')} ${data.reported_by})`;
                    confirmElement.className = confirmElement.className.replace('d-none', 'd-flex flex-row align-items-center mb-2 ');
                    pairingElement.style.display = 'block';
                    confirmBtn.style.display = 'inline-block';
                } else {
                    resultInfo += ` (${gettext('confirmed')})`;
                    confirmElement.className = confirmElement.className.replace('d-none', 'd-flex flex-row align-items-center mb-2 ');
                    pairingElement.style.display = 'block';
                }
            } else {
                var resultInfo = data.result;
                resultElement.className = resultElement.className.replace('d-none', 'd-flex flex-row align-items-center mb-2 ');
                reportBtn.style.display = 'block';
            }
            if (data.bye) {
                pairingHtml += ` - BYE`;
            }
            pairingHtml += `: ${resultInfo}`;
            pairingTextElement.innerHTML = pairingHtml;

            var player1Label = resultElement.querySelector(`label[for="player1-wins-${matchId}"]`);
            var player2Label = resultElement.querySelector(`label[for="player2-wins-${matchId}"]`);

            player1Label.innerHTML = `<strong>${gettext('Table')} ${data.table}:</strong> ${data.player1}`;
            player2Label.innerHTML = data.player2;
        })
        .catch(error => console.error('Error updating match info:', error));
    }

    
    var draftSlug = document.getElementById('admin-btns').dataset.draftSlug;
    var tournamentSlug = document.getElementById('admin-btns').dataset.tournamentSlug;
    var matchPanels = document.querySelectorAll('#match-panel');

    updateRoundStatus(tournamentSlug, draftSlug);

    setInterval(function() {
        updateRoundStatus(tournamentSlug, draftSlug);
    }, 120000);

    matchPanels.forEach(function(panel) {
        var matchId = panel.dataset.matchId;
        var tournamentSlug = panel.dataset.tournamentSlug;
        updateMatchInfo(tournamentSlug, matchId);

        setInterval(function() {
            updateMatchInfo(tournamentSlug, matchId);
        }, 120000); // 120 seconds
    });
});