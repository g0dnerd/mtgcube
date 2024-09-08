
document.addEventListener('DOMContentLoaded', function() {
    function updateTimetable(tournamentSlug) {
        var timetableElement = document.getElementById("timetable");
        var url = `/event-dashboard/${tournamentSlug}/~timetable/`;
        fetch(url)
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                timetableElement.innerHTML = `<h5>${gettext('My timetable')}:</h5><ul>` + 
                    data.timetable.map((draft) => {
                        const cubeUrl = `/cube/${draft.cube_slug}/`;
                        return `
                        <li>
                            ${gettext('Rounds')} ${draft.first_round} ${gettext('to')} ${draft.last_round}: <a href="${cubeUrl}" target="_blank">${draft.cube}</a>
                        </li>
                        `
                    }).join('') + '</ul>';
            }
        })
        .catch(error => console.error('Error fetching upcoming draft information:', error));
    }

    var tournamentSlug = document.getElementById('timetable').dataset.tournamentSlug;
    updateTimetable(tournamentSlug);

    setInterval(function() {
        updateTimetable(tournamentSlug);
    }, 120000); // 120 seconds
});