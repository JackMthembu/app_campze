/*===============================
parent/create_camp.html
=============================== */

function previewImage(input) {
    const preview = document.getElementById('imagePreview');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(input.files[0]);
    } else {
        preview.style.display = 'none';
    }
}

// Form validation for dates
document.querySelector('form').addEventListener('submit', function(e) {
    const startDate = new Date(document.querySelector('#start_date').value);
    const endDate = new Date(document.querySelector('#end_date').value);
    
    if (endDate < startDate) {
        e.preventDefault();
        alert('End date cannot be earlier than start date');
    }
});