// Get all sections
const recentSection = document.getElementById("recent");
const moviesSection = document.getElementById("movies");
const seriesSection = document.getElementById("series");

// Function to hide extra cards
function hideExtraCards(sectionId, maxVisible) {
    const section = document.getElementById(sectionId);
    const allCards = section.querySelectorAll(".card");
    allCards.forEach((card, index) => {
        if (index >= maxVisible) {
            card.classList.add('hidden');  // Add 'hidden' class to hide cards
        }
    });
}

// Initially hide extra cards for each section (3 for each as an example)
hideExtraCards("recent", 12);
hideExtraCards("movies", 12);
hideExtraCards("series", 12);

// Function to handle "Load More" logic for each section
function handleLoadMore(sectionId, loadMoreBtnId) {
    const section = document.getElementById(sectionId);
    const allCards = section.querySelectorAll(".card");
    const loadMoreBtn = document.getElementById(loadMoreBtnId);

    loadMoreBtn.addEventListener("click", function () {
        const visibleCards = section.querySelectorAll(".card:not(.hidden)").length;  // Get count of visible cards

        // Show the next 5 cards
        const nextVisibleCards = visibleCards + 5;
        for (let i = visibleCards; i < nextVisibleCards && i < allCards.length; i++) {
            allCards[i].classList.remove('hidden');  // Remove 'hidden' class to show card
        }

        // Hide button if all cards are shown
        if (nextVisibleCards >= allCards.length) {
            loadMoreBtn.style.display = "none";  // Hide the "Load More" button if all cards are visible
        }
    });
}

// Initialize "Load More" functionality for each section
handleLoadMore("recent", "load-more-recent");
handleLoadMore("movies", "load-more-movies");
handleLoadMore("series", "load-more-series");


