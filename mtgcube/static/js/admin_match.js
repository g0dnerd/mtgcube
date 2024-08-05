document.addEventListener('DOMContentLoaded', function() {
    function updateMatchInfo(tournamentSlug, matchId) {
        var infoElement = document.getElementById("pairing-" + matchId);
        var resultElement = document.getElementById("report-result-form-" + matchId);
        var url = `/admin-dashboard/${tournamentSlug}/~match/${matchId}/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            var pairingHtml = `<strong>${gettext('Table')} ${data.table}:</strong> ${data.player1} vs ${data.player2}`;
            var resultInfo = data.result;
            if (data.result !== 'Pending') {
                resultInfo += ` (${gettext('reported by')} ${data.reported_by})`;
                if (!data.result_confirmed) {
                    resultElement.style.display = 'block';
                }
            } else {
                resultElement.style.display = 'block';
            }
            if (data.bye) {
                pairingHtml += ` - BYE`;
            }
            pairingHtml += `: ${resultInfo}`;
            infoElement.innerHTML = pairingHtml;

            var player1Label = resultElement.querySelector(`label[for="player1-wins-${matchId}"]`);
            var player2Label = resultElement.querySelector(`label[for="player2-wins-${matchId}"]`);

            player1Label.innerHTML = `${data.player1} ${gettext('wins')}`;
            player2Label.innerHTML = `${data.player2} ${gettext('wins')}`;
        })
        .catch(error => console.error('Error updating match info:', error));
    }

    var matchPanels = document.querySelectorAll('#match-panel');
    matchPanels.forEach(function(panel) {
        var matchId = panel.dataset.matchId;
        var tournamentSlug = panel.dataset.tournamentSlug;
        updateMatchInfo(tournamentSlug, matchId);

        setInterval(function() {
            updateMatchInfo(tournamentSlug, matchId);
        }, 120000); // 120 seconds
    });
});