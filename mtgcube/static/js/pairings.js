document.addEventListener('DOMContentLoaded', function() {
    function updatePairingsInfo(tournamentSlug, draftId) {
        var pairingsContainer = document.getElementById("player-pairings");
        var pairingsElement = document.getElementById("pairings-" + draftId);
        var headerElement = document.getElementById("pairings-header-" + draftId);
        var url = `/event-dashboard/${tournamentSlug}/draft/${draftId}/~player-pairings-info/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                pairingsContainer.style.display = 'none';
            } else {
                var pairingsHtml = data.other_pairings.map(match => `
                    <li>${gettext('Table')} ${match.table}: ${match.player1} vs ${match.player2}</li>
                `).join('');

                if (data.bye) {
                    pairingsHtml += (`
                    <li>${data.bye} - BYE</li>
                    `);
                }
                headerElement.innerHTML = `<h5>${gettext('Other pairings')}:</h5>`;
                pairingsElement.innerHTML = pairingsHtml;
            }
        })
        .catch(error => console.error('Error updating pairings info:', error));
    }

    var tournamentSlug = document.getElementById('player-pairings').dataset.tournamentSlug;
    var draftId = document.getElementById('player-pairings').dataset.draftId;
    updatePairingsInfo(tournamentSlug, draftId);

    setInterval(function() {
        updatePairingsInfo(tournamentSlug, draftId);
    }, 120000); // 120 seconds
});