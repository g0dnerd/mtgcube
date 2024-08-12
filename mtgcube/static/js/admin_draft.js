document.addEventListener('DOMContentLoaded', function() {
    function updateDraftInfo(tournamentSlug, draftSlug, draftId) {
        var infoElement = document.getElementById("draft-name-" + draftId);
        var playersElement = document.getElementById("players-" + draftId);
        var statusElement = document.getElementById("draft-status-" + draftId);
        var url = `/admin-dashboard/${tournamentSlug}/${draftSlug}/~draft/`
        fetch(url)
        .then(response => response.json())
        .then(data => {
            var draftUrl = `/admin-dashboard/${tournamentSlug}/${draftSlug}/`;
            infoElement.innerHTML = `
            <h5><a href="${draftUrl}">Draft</a> playing ${data.cube}:</h5>
            `;

            if (data.paired) {
                if (data.finished) {
                    if (data.event_round > data.draft_round) {
                        var status = `Waiting for round ${data.draft_round + 1} pairings.`;
                    } else {
                        var status = 'Round finished.';
                    }
                } else {
                    var status='Round in progress.';
                }
            } else {
                if (data.seated) {
                    if (data.draft_round == 0) {
                        var status='Drafting portion in progress / Waiting for pairings.';
                    }
                } else {
                    var status='Waiting for seatings.';
                }
            }
            statusElement.innerHTML = `
            Status: ${status}
            `;

            var playersHtml = 'Players: ' + data.players.map((player, i) =>
            `${player}`).join(', ');
            playersElement.innerHTML = playersHtml;
        })
        .catch(error => console.error('Error updating draft info:', error));
    }
    
    var draftPanels = document.querySelectorAll('#draft-details');
    draftPanels.forEach(function(panel) {
        var tournamentSlug = panel.dataset.tournamentSlug;
        var draftSlug = panel.dataset.draftSlug;
        var draftId = panel.dataset.draftId;
        updateDraftInfo(tournamentSlug, draftSlug, draftId);
        setInterval(function() {
            updateDraftInfo(tournamentSlug, draftSlug, draftId);
        }, 120000); // 120 seconds
    });
});