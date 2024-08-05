
document.addEventListener('DOMContentLoaded', function() {

    function getUploadHtml(data) {
        if (!data.checked_in) {
            var checkinUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkin-upload/`;
            return `
                <div class="pool-info-check-in-missing">
                    <h5>${gettext('You are not yet checked in')}. ${gettext('Please')} <a href="${checkinUrl}">${gettext('upload your pool')}</a> ${gettext('once you have finished drafting.')}</h5>
                </div>
            `;
        }
        
        var checkinPoolUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkin-pool/`;
        let html = `
            <div class="pool-info-checked-in">
                <h5>${gettext('You are checked in and good to go')}!</h5>
                <a href="${checkinPoolUrl}">${gettext('My pool')}</a>
            </div>
        `;

        if (data.checked_out) {
            var checkoutPoolUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkout-pool/`;
            html = `
                <div class="pool-info-checked-out">
                    <h5>${gettext('You have checked out and are good to go!')}</h5>
                    <a href="${checkoutPoolUrl}">${gettext('My pool')}</a>
                </div>
            `;
        } else {
            var checkoutUrl = `/event-dashboard/${tournamentSlug}/${draftSlug}/checkout-upload/`;
            html += `
                <div class="pool-info-check-out-missing">
                    <h5>${gettext('To check out, please')} <a href="${checkoutUrl}">${gettext('upload your pool')}</a> ${gettext('after you have finished all your matches.')}</h5>
                </div>
            `;
        }

        return html;
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
    console.log(draftSlug);
    var poolElement = document.getElementById("deck-upload");
    updateStatusInfo(tournamentSlug, draftSlug);
    setInterval(function() {
        updateStatusInfo(tournamentSlug, draftSlug);
    }, 120000); // 120 seconds
});