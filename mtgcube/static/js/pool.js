
document.addEventListener('DOMContentLoaded', function() {

    function getUploadHtml(data) {
        if (!data.checked_in) {
            var checkinUrl = `/event-dashboard/${tournamentSlug}/my-current-draft/check-in/`;
            return `
                <div class="pool-info-check-in-missing">
                    <h5>${gettext('You are not yet checked in')}. ${gettext('Please')} <a href="${checkinUrl}">${gettext('upload your pool')}</a> ${gettext('once you have finished drafting.')}</h5>
                </div>
            `;
        }
        
        var checkinPoolUrl = `/event-dashboard/${tournamentSlug}/my-current-draft/checkin-deck-upload/`;
        let html = `
            <div class="pool-info-checked-in">
                <h5>${gettext('You are checked in and good to go')}!</h5>
                <a href="${checkinPoolUrl}">${gettext('My pool')}</a>
            </div>
        `;

        if (data.checked_out) {
            var checkoutPoolUrl = `/event-dashboard/${tournamentSlug}/my-current-draft/checkout-deck-upload/`;
            html = `
                <div class="pool-info-checked-out">
                    <h5>${gettext('You have checked out and are good to go!')}</h5>
                    <a href="${checkoutPoolUrl}">${gettext('My pool')}</a>
                </div>
            `;
        } else {
            var checkoutUrl = `/event-dashboard/${tournamentSlug}/my-current-draft/check-out/`;
            html += `
                <div class="pool-info-check-out-missing">
                    <h5>${gettext('To check out, please')} <a href="${checkoutUrl}">${gettext('upload your pool')}</a> ${gettext('after you have finished all your matches.')}</h5>
                </div>
            `;
        }

        return html;
    }

    function updateStatusInfo() {
        var url = `/event-dashboard/${tournamentSlug}/draft/${draftId}/~player-basic-info/`;
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
    var draftId = document.getElementById('deck-upload').dataset.draftId;
    var poolElement = document.getElementById("deck-upload");
    updateStatusInfo(tournamentSlug, draftId);
    setInterval(function() {
        updateStatusInfo(tournamentSlug, draftId);
    }, 120000); // 120 seconds
});