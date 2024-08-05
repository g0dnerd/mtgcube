document.addEventListener('DOMContentLoaded', function() {
    function updateSeatings(tournamentSlug, draftSlug) {
        var seatingsContainer = document.getElementById("player-seatings");
        var seatingsElement = document.getElementById("seatings");
        var headerElement = document.getElementById("seatings-header");
        var infoElement = document.getElementById("seatings-info");
        var url = `/event-dashboard/${tournamentSlug}/${draftSlug}/~seatings/`;
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
    var draftSlug = document.getElementById('player-seatings').dataset.draftSlug;

    updateSeatings(tournamentSlug, draftSlug);

    setInterval(function() {
        updateSeatings(tournamentSlug, draftSlug);
    }, 600000); // 120 seconds
});