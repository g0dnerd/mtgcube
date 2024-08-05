document.addEventListener('DOMContentLoaded', function() {
    function updatePlayerInfo(tournamentSlug, draftSlug) {
        var infoElement = document.getElementById("player-list-inner");
        var url = `/event-dashboard/${tournamentSlug}/${draftSlug}/~players/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            infoElement.innerHTML = data.players.map((player) => `${player}`).join(', ');
        })
        .catch(error => console.error('Error updating match info:', error));
    }
    
    var tournamentSlug = document.getElementById('player-list').dataset.tournamentSlug;
    var draftSlug = document.getElementById('player-list').dataset.draftSlug;
    updatePlayerInfo(tournamentSlug, draftSlug);

    setInterval(function() {
        updatePlayerInfo(tournamentSlug, draftSlug);
    }, 120000); // 120 seconds
});