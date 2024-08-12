
document.addEventListener('DOMContentLoaded', function() {

    function getUploadHtml(data) {
        if (!data.checked_in) {
            var containerElement = document.getElementById("match-info-list");
            if (containerElement) {
                if (document.getElementById("match-info-list").dataset.bye == 'True') {
                    var oppHeaderElement = document.getElementById("opponent-header");
                    var oppTextElement = document.getElementById("opponent-text");
                    var oppElement = document.getElementById("my-opponent");
                    var child = oppTextElement.firstChild;
                    child.textContent = '';
                    child.nextSibling.textContent = '';
                    child.nextSibling.nextSibling.textContent = '';
                    var checkInUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkin-upload/`;
                    oppElement.innerHTML = gettext('Your pairing will be revealed once you have ') + `<a href="${checkInUrl}">` + gettext('checked in') + `</a>` + '.';
                    oppHeaderElement.style.display = 'block';
                }
            }
            var checkinUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkin-upload/`;
            var checkinPoolUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkin-pool/`;
            return `
                <div class="pool-info-check-in-missing">
                    <h5>${gettext('You have not yet checked in')}. ${gettext('Please')} <a href="${checkinUrl}">${gettext('upload your pool')}</a> ${gettext('once you have finished drafting.')}</h5>
                </div>
            `;
        }
        var oppHeaderElement = document.getElementById("opponent-header");
        if (oppHeaderElement) {
            oppHeaderElement.style.display = 'block';
        }
        
        if (data.draft_finished) {
            if (data.checked_out) {
                var checkoutPoolUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkout-pool/`;
                return `
                    <div class="pool-info-checked-out">
                        <h5>${gettext('You have successfully checked out')}!</h5>
                        <a href="${checkoutPoolUrl}">${gettext('My pool')}</a>
                    </div>
                `;
            }    
            var checkoutUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkout-upload/`;
            return `
                <div class="pool-info-check-out-missing">
                    <h5>${gettext('You have not yet checked out')}. ${gettext('Please')} 
                        <a href="${checkoutUrl}">${gettext('upload your pool')}</a> ${gettext('after your last match.')}
                    </h5>
                </div>
            `;
        }

        var checkinPoolUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkin-pool/`;
        return `
            <div class="pool-info-checked-in">
                <h5>${gettext('You have successfully checked in')}!</h5>
                <a href="${checkinPoolUrl}">${gettext('My pool')}</a>
            </div>
        `;
    }

    function updateStatusInfo(tournamentSlug, draftSlug) {
        var url = `/event-dashboard/${tournamentSlug}/${draftSlug}/~player-basic-info/`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (!data.draft_seated) {
                    poolElement.style.display = 'none';
                } else {
                    if (!data.error) {
                        poolElement.innerHTML = getUploadHtml(data);
                        poolElement.style.display = 'block';
                    }
                }
            })
            .catch(error => console.error('Error fetching status information:', error));
    }

    var tournamentSlug = document.getElementById('deck-upload').dataset.tournamentSlug;
    var draftSlug = document.getElementById('deck-upload').dataset.draftSlug;
    var poolElement = document.getElementById("deck-upload");
    updateStatusInfo(tournamentSlug, draftSlug);
    setInterval(function() {
        updateStatusInfo(tournamentSlug, draftSlug);
    }, 120000); // 120 seconds
});