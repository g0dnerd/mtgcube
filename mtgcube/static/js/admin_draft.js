document.addEventListener('DOMContentLoaded', function() {
    function updateDraftInfo(tournamentSlug, draftSlug, draftId) {
        var infoElement = document.getElementById("draft-name-" + draftId);
        var playersElement = document.getElementById("players-" + draftId);
        var statusElement = document.getElementById("draft-status-" + draftId);
        var url = `/admin-dashboard/${tournamentSlug}/~draft/${draftId}/`
        fetch(url)
        .then(response => response.json())
        .then(data => {
            var draftUrl = `/admin-dashboard/${draftSlug}`;
            infoElement.innerHTML = `
            <h5><a href="${draftUrl}">Draft</a> playing ${data.cube}:</h5>
            `;

            if (data.paired) {
                if (data.finished) {
                    var status='Round finished.';
                } else {
                    var status='Round in progress.';
                }
            } else {
                if (data.seated) {
                    var status='Drafting portion in progress.';
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