// FLASHCARDS //

// Card Flip Functionality
document.addEventListener("DOMContentLoaded", function () { // Wait for the DOM to be fully loaded
    document.querySelectorAll(".card-container").forEach(function (cardContainer) { // For each card container
        cardContainer.addEventListener("click", function () { // Listen for when the card container is clicked
            cardContainer.classList.toggle("flipped"); // change the 'flipped' class on the card container
        });
    });
});

// Modal Functionality
// Note: by doing it in the JavaScript, we make the process smoother than if we were to implement a backend solution. We edit the DOM directly, rather than having to reload the page.
function openEditModal(id, username, email, role) { // Opens the edit modal with the given user data
    document.getElementById('edit_index').value = id;
    document.getElementById('new_username').value = username;
    document.getElementById('new_role').value = role;
    document.getElementById('editUserModal').style.display = 'block';
}

function closeEditModal() { // Closes the edit modal
    document.getElementById('editUserModal').style.display = 'none';
}