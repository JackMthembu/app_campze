let autocomplete;
let placeData = {};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Google Places Autocomplete
    autocomplete = new google.maps.places.Autocomplete(
        document.getElementById('schoolSearch'),
        {
            types: ['school'],
            fields: ['name', 'formatted_address', 'address_components', 'geometry']
        }
    );

    // Handle place selection
    autocomplete.addListener('place_changed', function() {
        const place = autocomplete.getPlace();
        if (!place.geometry) {
            return;
        }

        // Extract and populate form data
        document.getElementById('schoolName').value = place.name;
        document.getElementById('schoolAddress').value = place.formatted_address;
        document.getElementById('schoolLatitude').value = place.geometry.location.lat();
        document.getElementById('schoolLongitude').value = place.geometry.location.lng();

        // Extract city, state, and country information
        for (const component of place.address_components) {
            if (component.types.includes('locality')) {
                document.getElementById('schoolCity').value = component.long_name;
            }
        }

        // Store place data for API calls
        placeData = {
            address_components: place.address_components,
            geometry: place.geometry
        };
    });
});

function submitSchool() {
    const form = document.getElementById('addSchoolForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Add place data
    data.place_data = placeData;

    fetch('{{ url_for("parent.add_school") }}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            // Add new school to select options
            const select = document.getElementById('school_id');
            const option = new Option(data.school.name, data.school.id, true, true);
            select.add(option);
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addSchoolModal'));
            modal.hide();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while adding the school. Please try again.');
    });
}

// Original child form submission code
document.getElementById('addChildForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    fetch('{{ url_for("parent.add_child") }}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            window.location.href = '{{ url_for("parent.manage_children") }}';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while adding the child. Please try again.');
    });
});