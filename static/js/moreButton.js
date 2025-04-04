document.addEventListener("DOMContentLoaded", function () {
    const moreButton = document.querySelector(".button-more");
    const modal = document.getElementById("optionsModal");
    const closeModalButton = document.getElementById("closeModal");

    // Fetch the item ID
    const itemId = document.querySelector('.detail-action-buttons').getAttribute('data-item-id');

    // Toggle modal visibility on "More" button click
    moreButton.addEventListener("click", function() {
        // Check if the modal is already visible
        const isModalVisible = modal.style.display === 'block';

        if (isModalVisible) {
            // If modal is visible, close it
            modal.style.display = 'none';
        } else {
            // Open the modal next to the button
            const buttonRect = moreButton.getBoundingClientRect();
            const buttonWidth = buttonRect.width;
            const modalWidth = modal.offsetWidth;

            // Position the modal to the left of the button
            modal.style.top = `${buttonRect.top + window.scrollY + moreButton.offsetHeight + 5}px`; // Position below the button
            modal.style.left = `${buttonRect.left + window.scrollX - modalWidth - 210}px`; // Position to the left of the button

            // Show the modal
            modal.style.display = 'block';
        }
    });

    // Close modal when the "Close" button inside the modal is clicked
    closeModalButton.addEventListener("click", function () {
        modal.style.display = "none"; // Hide the modal
    });

    // Close the modal if the user clicks outside of the modal content
    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.style.display = "none"; // Hide the modal if clicked outside
        }
    });


    window.moreOptions = function() {
        console.log("More Options clicked!");
        modal.style.display = "none"; // Close modal after action
    };

    // Hide modal on window resize
    window.addEventListener("resize", function () {
        if (modal.style.display === 'block') {
            modal.style.display = 'none'; // Hide modal if it's visible
        }
    });
});
