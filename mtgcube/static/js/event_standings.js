document.addEventListener('DOMContentLoaded', function() {
    function updateStandings(eventSlug) {
        var standingsElement = document.getElementById("event-standings-" + eventSlug);
        var headerElement = document.getElementById("event-standings-header-" + eventSlug);
        var infoElement = document.getElementById("event-standings-info-" + eventSlug);
        var containerElement = document.getElementById('standings-container');
        var url = `/event-dashboard/${eventSlug}/~standings/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                headerElement.innerHTML = `${gettext('Event standings after round')} ${data.current_round}:`;
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
            }
        })
        .catch(error => console.error('Error updating event standings:', error));
    }
    
    var eventSlug = document.getElementById('standings-container').dataset.tournamentSlug;
    updateStandings(eventSlug);

    setInterval(function() {
        updateStandings(eventSlug);
    }, 120000); // 120 seconds
});