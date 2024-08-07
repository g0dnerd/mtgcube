document.addEventListener('DOMContentLoaded', function() {
    function updatePairingsInfo(tournamentSlug, draftSlug) {
        var pairingsContainer = document.getElementById("player-pairings");
        var pairingsElement = document.getElementById("pairings");
        var headerElement = document.getElementById("pairings-header");
        var url = `/event-dashboard/${tournamentSlug}/${draftSlug}/~player-pairings/`;
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
                headerElement.innerHTML = `${gettext('Other pairings')}:`;
                pairingsElement.innerHTML = pairingsHtml;
            }
        })
        .catch(error => console.error('Error updating pairings info:', error));
    }

    var tournamentSlug = document.getElementById('player-pairings').dataset.tournamentSlug;
    var draftSlug = document.getElementById('player-pairings').dataset.draftSlug;
    updatePairingsInfo(tournamentSlug, draftSlug);

    setInterval(function() {
        updatePairingsInfo(tournamentSlug, draftSlug);
    }, 120000); // 120 seconds
});