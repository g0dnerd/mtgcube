document.addEventListener('DOMContentLoaded', function() {
    function updatePlayerInfo(tournamentSlug, draftId) {
        var infoElement = document.getElementById("player-list-" + draftId);
        var url = `/event-dashboard/${tournamentSlug}/draft/${draftId}/~players/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            infoElement.innerHTML = data.players.map((player) => `${player}`).join(', ');
        })
        .catch(error => console.error('Error updating match info:', error));
    }
    
    var tournamentSlug = document.getElementById('player-list').dataset.tournamentSlug;
    var draftId = document.getElementById('player-list').dataset.draftId;
    updatePlayerInfo(tournamentSlug, draftId);

    setInterval(function() {
        updatePlayerInfo(tournamentSlug, draftId);
    }, 120000); // 120 seconds
});