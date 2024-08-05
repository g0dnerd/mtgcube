function fetchDraftDetails(tournamentSlug) {
    var url = `/event-dashboard/${tournamentSlug}/~player-draft-info/`;
    fetch(url)
    .then(response => response.json())
    .then(data => {
        const draftInfoElement = document.getElementById("draft-info-header");
        const cubeInfoElement = document.getElementById("player-cube-info");
        const statusElement = document.getElementById('player-signup-status');
        if (!data.error) {
            var currentDraftUrl = `/event-dashboard/${tournamentSlug}/my-current-draft/`;
            if (data.current_round == 0 && !data.seated) {
                draftInfoElement.innerHTML = `
                <h5 class="draft-disabled">
                    ${gettext('Waiting for draft to start')}
                </h5>
                `;
            } else {
                draftInfoElement.innerHTML = `
                <h5>
                    <a href="${currentDraftUrl}">${gettext('My current draft')}</a>
                </h5>
                `;
            }
            const cubeUrl = `/cube/${data.cube_slug}`;
            cubeInfoElement.innerHTML = `
            ${gettext('Cube list')}: <a href=${cubeUrl} target="_blank">
                ${data.cube_name}
            </a>
            `;
            if (data.current_round >= 1) {
                statusElement.style.display = 'none';
            }
        } else {
            console.log(data.error);
        }
    })
    .catch(error => console.error('Error fetching draft information:', error));
}

function fetchAnnouncement(tournamentSlug) {
    var url = `/event-dashboard/${tournamentSlug}/~announcement/`;
    fetch(url)
    .then(response => response.json())
    .then(data => {
        const announcementElement = document.getElementById('announcement');
        if (data.error) {
            announcementElement.style.display = 'none';
        } else {
            announcementElement.innerHTML = `
            <h5>
                ${gettext('Event announcement')}: ${data.announcement}
            </h5>
            `;
            announcementElement.style.display = 'block';
        }
    })
    .catch(error => console.error('Error fetching event information', error));
}

// Initial formatting
document.addEventListener('DOMContentLoaded', () => {
    var tournamentSlug = document.getElementById('dashboard-container').dataset.tournamentSlug;
    fetchDraftDetails(tournamentSlug);
    fetchAnnouncement(tournamentSlug);
    setInterval(function() {
        fetchDraftDetails(tournamentSlug);
    }, 600000); // 120 seconds
    setInterval(function() {
        fetchAnnouncement(tournamentSlug);
    }, 600000); // 120 seconds
});