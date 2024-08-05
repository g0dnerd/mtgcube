document.addEventListener('DOMContentLoaded', function() {
    function updateSeatings(tournamentSlug, draftId) {
        var seatingsContainer = document.getElementById("player-seatings");
        var seatingsElement = document.getElementById("seatings-" + draftId);
        var headerElement = document.getElementById("seatings-header-" + draftId);
        var infoElement = document.getElementById("seatings-info-" + draftId);
        var url = `/event-dashboard/${tournamentSlug}/draft/${draftId}/~seatings/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            headerElement.innerHTML = 'Seatings:';
            if (!data.error) {
                seatingsElement.innerHTML = data.seatings.map((player, i) => `
                    <li>${player.name}</li>
                `).join('');
                seatingsContainer.style.display = 'block';
            } else {
                if (data.error == "Draft has not been seated yet.") {
                    infoElement.innerHTML = `Waiting for seatings.`;
                    seatingsContainer.style.display = 'block';
                }
            }
        })
        .catch(error => console.error('Error updating match info:', error));
    }

    var tournamentSlug = document.getElementById('player-seatings').dataset.tournamentSlug;
    var draftId = document.getElementById('player-seatings').dataset.draftId;

    updateSeatings(tournamentSlug, draftId);

    setInterval(function() {
        updateSeatings(tournamentSlug, draftId);
    }, 600000); // 120 seconds
});