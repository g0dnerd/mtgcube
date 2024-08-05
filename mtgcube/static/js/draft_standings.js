document.addEventListener('DOMContentLoaded', function() {
    function updateStandings(tournamentSlug, draftSlug) {
        var standingsElement = document.getElementById("draft-standings");
        var headerElement = document.getElementById("draft-standings-header");
        var infoElement = document.getElementById("draft-standings-info");
        var containerElement = document.getElementById('standings-container');
        var url = `/event-dashboard/${tournamentSlug}/${draftSlug}/~draft-standings/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                headerElement.innerHTML = `${gettext('Draft standings after round')} ${data.current_round}:`;
                var standingsHtml = data.standings.map((player, i) => `
                    <tr>
                        <td style="text-align: center; padding-right: 40px;">${i + 1}</td>
                        <td style="text-align: center; padding-right: 40px;">${player.name}</td>
                        <td style="text-align: center; padding-right: 40px;">${player.score}</td>
                        <td style="text-align: center; padding-right: 40px;">${player.omw}</td>
                        <td style="text-align: center; padding-right: 40px;">${player.pgw}</td>
                        <td style="text-align: center; padding-right: 40px;">${player.ogw}</td>
                    </tr>
                `).join('');
                var tbody = standingsElement.querySelector('tbody');
                tbody.innerHTML = `${standingsHtml}`;
                containerElement.style.display = 'block';
            } else {
                if (data.error == 'No draft standings yet') {
                    headerElement.innerHTML = `${gettext('Draft standings')}:`;
                    infoElement.innerHTML = `${gettext('Draft standings will display here after the first round finishes')}.`;
                    containerElement.style.display = 'block';
                }
            }
        })
        .catch(error => console.error('Error updating match info:', error));
    }

    var tournamentSlug = document.getElementById('standings-container').dataset.tournamentSlug;
    var draftSlug = document.getElementById('standings-container').dataset.draftSlug;
    updateStandings(tournamentSlug, draftSlug);

    setInterval(function() {
        updateStandings(tournamentSlug, draftSlug);
    }, 120000); // 120 seconds
});