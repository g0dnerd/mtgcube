document.addEventListener('DOMContentLoaded', function() {
    function updateMatchInfo(tournamentSlug) {
        var matchElement = document.getElementById("current-match");
        var url = `/event-dashboard/${tournamentSlug}/~player-match-preview/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                if (data.bye) {
                    matchElement.innerHTML = `<h5>${gettext('You have the bye this round')}.</h5>`;
                } else {
                    var infoOut = `${data.table}: ${data.opponent} ${data.opp_pronouns}`;
                    matchElement.innerHTML = gettext('My current opponent at table ') + infoOut;
                }
                matchElement.style.display = 'block';
            } else {
                if (data.error == 'No checkin.') {
                    var checkInUrl = `/event-dashboard/${tournamentSlug}/${data.draft.slug}/checkin-upload/`;
                    matchElement.innerHTML = gettext(
                        'Your pairing will be revealed once you have') + `<a href="${checkInUrl}">` + gettext('checked in') + `</a>` + '.';
                    matchElement.style.display = 'block';
                }
                else if (data.error == "No match yet.") {
                    matchElement.innerHTML = `
                        ${gettext('Waiting for pairings')}
                    `;
                    matchElement.style.display = 'block';
                }
            }
        })
        .catch(error => console.error('Error fetching current match information:', error));
    }

    var tournamentSlug = document.getElementById('current-match').dataset.tournamentSlug;
    updateMatchInfo(tournamentSlug);

    setInterval(function() {
        updateMatchInfo(tournamentSlug);
    }, 120000); // 120 seconds
});