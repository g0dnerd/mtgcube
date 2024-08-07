document.addEventListener('DOMContentLoaded', function() {
    function updateMatchInfo(tournamentSlug, draftSlug, matchId) {
        var resultElement = document.getElementById("result-info");
        var formElement = document.getElementById(`report-result-form-${matchId}`);
        var oppElement = document.getElementById("my-opponent");
        var oppHeaderElement = document.getElementById("opponent-header");
        var oppTextElement = document.getElementById("opponent-text");
        var confirmButtonElement = document.getElementById("confirm-result-btn");
        var url = `/event-dashboard/${tournamentSlug}/${draftSlug}/${matchId}/~player-match/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                var winner = data.winner ? `${data.winner} wins` : '';
                oppElement.innerHTML = `${data.opponent} ${data.opp_pronouns}`;
                resultElement.innerHTML = data.result !== "Pending" ? `<p class="match-result">${gettext('Result')}: ${winner} ${data.result}</p>` : '';

                oppHeaderElement.style.display = 'block';

                if (data.result === "Pending") {
                    formElement.style.display = 'block';
                    confirmButtonElement.style.display = 'none';
                    resultElement.style.display = 'block';
                } else {
                    formElement.style.display = 'none';
                    if (!data.result_confirmed && data.name !== data.reported_by) {
                        confirmButtonElement.style.display = 'block';
                    } else {
                        confirmButtonElement.style.display = 'none';
                    }
                    resultElement.style.display = 'block';
                }
            } else {
                if (data.error == 'No checkin.') {
                    var child = oppTextElement.firstChild;
                    child.textContent = '';
                    child.nextSibling.textContent = '';
                    child.nextSibling.nextSibling.textContent = '';
                    var checkInUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkin-upload/`;
                    oppElement.innerHTML = gettext('Your pairing will be revealed once you have ') + `<a href="${checkInUrl}">` + gettext('checked in') + `</a>` + '.';
                    oppHeaderElement.style.display = 'block';
                }
            }
            
        })
        .catch(error => console.error('Error updating match info:', error));
    }

    if (document.getElementById("match-info-list").dataset.bye == 'False') {
        var tournamentSlug = document.getElementById('match-details').dataset.tournamentSlug;
        var draftSlug = document.getElementById('match-details').dataset.draftSlug;
        var matchId = document.getElementById('match-details').dataset.matchId;
        updateMatchInfo(tournamentSlug, draftSlug, matchId);

        setInterval(function() {
            updateMatchInfo(tournamentSlug, draftSlug, matchId);
        }, 120000); // 120 seconds
    }
});
