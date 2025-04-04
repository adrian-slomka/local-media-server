document.addEventListener("DOMContentLoaded", function () {
    const likedButton = document.querySelector(".button-liked");
    const itemId = document.querySelector('.detail-action-buttons').getAttribute('data-item-id');



    // Fetch the user liked status from the backend database
    fetch(`/get_liked_status/${itemId}`)
        .then(response => response.json())
        .then(data => {
            if (data.liked !== undefined) {
                // Apply the initial liked status to the button
                updateLikedButton(data.liked);
            }
        })
        .catch(error => {
            console.log('Error fetching watchlist status:', error);
        });

    // Handle click event on the liked button
    likedButton.addEventListener("click", () => {
        const newLikedStatus = likedButton.classList.contains('filled') ? 0 : 1;

        console.log(`Sending liked status: ${newLikedStatus} for item ID: ${itemId}`); // Debug

        // Send the updated liked status to the backend
        fetch('/submit_liked', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                liked: newLikedStatus,
                item_id: itemId  
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response from server:', data); // Debug
            updateLikedButton(newLikedStatus); 
        })
        .catch(error => {
            console.log('Error setting liked status:', error);
        });
    });



    // Function to visually update the liked button based on the status
    function updateLikedButton(likedStatus) {
        if (likedStatus === 1) {
            likedButton.classList.add('filled');  // Add "filled" class to visually change the button (e.g., color)
        } else {
            likedButton.classList.remove('filled');  // Remove the "filled" class if unliked
        }
    }
});

// Handle click event on the remove button in watchlist
function submitRemove(remove) {
    const _itemId_ = remove;

    // Send the updated liked status to the backend
    fetch('/submit_liked', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            liked: 0,
            item_id: _itemId_  
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Item removed from watchlist:', data);
        location.reload();
    })
    .catch(error => {
        console.log('Error removing from watchlist:', error);
    });
}