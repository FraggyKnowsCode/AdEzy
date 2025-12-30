// ========================================
// AdEzy - Main JavaScript (Client-Side Logic)
// ========================================

// Global variables
let allGigs = [];
let currentUser = null;
let lastScrollY = window.scrollY;
let displayedGigsCount = 0;
const GIGS_PER_PAGE = 15;

// ========================================
// Show More Gigs Function
// ========================================
function showMoreGigs() {
    renderGigs(allGigs, true);
}

// ========================================
// Initialize App on Page Load
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('AdEzy initialized');
    
    // Load initial data
    loadGigsForSearch(); // Always load gigs for search functionality
    loadUserBalance();
    loadSellerEarnings();
    
    // Auto-refresh balance every 10 seconds to catch admin approvals
    setInterval(() => {
        loadUserBalance();
    }, 10000); // 10 seconds
    
    // Load seller's gigs if on dashboard
    if (document.getElementById('my-gigs-container')) {
        loadMyGigs();
    }
    
    // Load conversations for messages dropdown
    if (document.getElementById('conversations-list')) {
        loadConversations();
    }
    
    // Load notifications
    if (document.getElementById('notifications-list')) {
        loadNotifications();
    }
    
    // Set up event listeners
    setupSearchListener();
    setupDashboardTabs();
    setupScrollBehavior();
    
    // Check if on dashboard page
    if (document.querySelector('#buyer-section')) {
        loadBuyerOrders();
        loadSellerOrders();
    }
    
    // Handle anchor scroll on page load
    if (window.location.hash) {
        setTimeout(() => {
            const element = document.querySelector(window.location.hash);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 500);
    }
});

// Setup scroll behavior for sticky navbar
function setupScrollBehavior() {
    let scrollTimeout;
    
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        // Add/remove class based on scroll direction
        if (currentScrollY > 100) {
            if (currentScrollY > lastScrollY) {
                // Scrolling down
                document.body.classList.add('scrolled-down');
            } else {
                // Scrolling up
                document.body.classList.remove('scrolled-down');
            }
        } else {
            // Near top
            document.body.classList.remove('scrolled-down');
        }
        
        lastScrollY = currentScrollY;
    });
}

// Filter by category and scroll to popular services
function filterByCategory(categoryName) {
    // Update URL with category parameter
    window.location.href = `/?category=${encodeURIComponent(categoryName)}#popular-services`;
}

// Make filterByCategory available globally
window.filterByCategory = filterByCategory;


// ========================================
// Dynamic Gig Rendering (DOM Manipulation)
// ========================================
// Load gigs for search (works on all pages)
async function loadGigsForSearch() {
    try {
        // Check for URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const category = urlParams.get('category');
        const filter = urlParams.get('filter');
        
        // Build API URL with parameters
        let apiUrl = '/api/gigs/';
        const params = [];
        if (category) params.push(`category=${encodeURIComponent(category)}`);
        if (filter) params.push(`filter=${encodeURIComponent(filter)}`);
        if (params.length > 0) {
            apiUrl += '?' + params.join('&');
        }
        
        // Reset pagination
        displayedGigsCount = 0;
        
        // Fetch gigs from Django backend
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error('Failed to fetch gigs');
        }
        
        const data = await response.json();
        allGigs = data.gigs;
        console.log(`Loaded ${allGigs.length} gigs for search`);
        
        // If we're on home page, render the gigs
        const container = document.querySelector('#gig-container');
        if (container) {
            renderGigs(allGigs);
            // Update search results info if category/filter is active
            updateFilterInfo(category, filter, allGigs.length);
        }
    } catch (error) {
        console.error('Error loading gigs for search:', error);
        allGigs = [];
    }
}

async function loadGigs() {
    const container = document.querySelector('#gig-container');
    
    if (!container) return;
    
    // Show loading state
    container.innerHTML = '<div class="loading">Loading gigs...</div>';
    
    try {
        // Fetch gigs from Django backend
        const response = await fetch('/api/gigs/');
        
        if (!response.ok) {
            throw new Error('Failed to fetch gigs');
        }
        
        const data = await response.json();
        allGigs = data.gigs;
        
        // Render gigs
        renderGigs(allGigs);
        
    } catch (error) {
        console.error('Error loading gigs:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3>⚠️ Error Loading Gigs</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

function renderGigs(gigs, append = false) {
    const container = document.querySelector('#gig-container');
    const searchResultsInfo = document.getElementById('search-results-info');
    const searchResultsText = document.getElementById('search-results-text');
    const searchInput = document.querySelector('#search-input');
    const showMoreContainer = document.getElementById('show-more-container');
    const gigsCountInfo = document.getElementById('gigs-count-info');
    
    if (!container) {
        console.log('Gig container not found on this page');
        return;
    }
    
    console.log(`Rendering ${gigs.length} gigs (append: ${append})`);
    
    // Show/hide search results info
    if (searchResultsInfo && searchInput && searchInput.value.trim() !== '') {
        const searchTerm = searchInput.value.trim();
        if (searchResultsText) {
            searchResultsText.textContent = `Found ${gigs.length} gig${gigs.length !== 1 ? 's' : ''} matching "${searchTerm}"`;
        }
        searchResultsInfo.style.display = 'block';
    } else if (searchResultsInfo) {
        searchResultsInfo.style.display = 'none';
    }
    
    // Clear container if not appending
    if (!append) {
        container.innerHTML = '';
        displayedGigsCount = 0;
    }
    
    // Check if empty
    if (gigs.length === 0) {
        const searchTerm = searchInput ? searchInput.value.trim() : '';
        container.innerHTML = `
            <div class="empty-state">
                <h3>No gigs found</h3>
                <p>${searchTerm ? `No results for "${searchTerm}". Try different keywords.` : 'Check back later for new services.'}</p>
            </div>
        `;
        if (showMoreContainer) showMoreContainer.style.display = 'none';
        return;
    }
    
    // Determine how many gigs to show
    const startIndex = append ? displayedGigsCount : 0;
    const endIndex = Math.min(startIndex + GIGS_PER_PAGE, gigs.length);
    const gigsToShow = gigs.slice(startIndex, endIndex);
    
    // Create gig cards dynamically
    gigsToShow.forEach((gig, index) => {
        // Create card container
        const card = document.createElement('div');
        card.className = 'gig-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        // Create image element
        const image = document.createElement('img');
        image.className = 'gig-card-image';
        image.src = gig.image_url;
        image.alt = gig.title;
        image.loading = 'lazy';
        
        // Create content container
        const content = document.createElement('div');
        content.className = 'gig-card-content';
        
        // Create title
        const title = document.createElement('h3');
        title.className = 'gig-card-title';
        title.textContent = gig.title;
        
        // Create seller name
        const seller = document.createElement('p');
        seller.className = 'gig-card-seller';
        seller.textContent = `by ${gig.seller_name}`;
        
        // Create rating display (if rating exists)
        if (gig.rating && gig.rating > 0) {
            const ratingDiv = document.createElement('div');
            ratingDiv.className = 'gig-card-rating';
            ratingDiv.innerHTML = `
                <span class="rating-stars">⭐ ${gig.rating.toFixed(1)}</span>
                <span class="rating-reviews">(${gig.total_reviews} reviews)</span>
            `;
            content.appendChild(ratingDiv);
        }
        
        // Create category badge
        const category = document.createElement('span');
        category.className = 'gig-card-category';
        category.textContent = gig.category;
        
        // Append to content
        content.appendChild(title);
        content.appendChild(seller);
        content.appendChild(category);
        
        // Create footer
        const footer = document.createElement('div');
        footer.className = 'gig-card-footer';
        
        // Create price
        const price = document.createElement('div');
        price.className = 'gig-card-price';
        price.textContent = `${gig.price} Taka`;
        
        // Create view details button
        const orderButton = document.createElement('button');
        orderButton.className = 'btn-order';
        orderButton.textContent = 'View Details';
        orderButton.onclick = (e) => {
            e.stopPropagation();
            window.location.href = '/gig/' + gig.id + '/';
        };
        
        // Append to footer
        footer.appendChild(price);
        footer.appendChild(orderButton);
        
        // Make card clickable
        card.style.cursor = 'pointer';
        card.onclick = () => {
            window.location.href = '/gig/' + gig.id + '/';
        };
        
        // Assemble card
        card.appendChild(image);
        card.appendChild(content);
        card.appendChild(footer);
        
        // Add to container
        container.appendChild(card);
    });
    
    // Update displayed count
    displayedGigsCount = endIndex;
    
    // Show/hide "Show More" button
    if (showMoreContainer) {
        if (displayedGigsCount < gigs.length) {
            showMoreContainer.style.display = 'block';
            if (gigsCountInfo) {
                gigsCountInfo.textContent = `Showing ${displayedGigsCount} of ${gigs.length} gigs`;
            }
        } else {
            showMoreContainer.style.display = 'none';
        }
    }
}

// ========================================
// Search Functionality (Client-Side)
// ========================================
function setupSearchListener() {
    const searchInput = document.querySelector('#search-input');
    const suggestionsContainer = document.getElementById('search-suggestions');
    
    if (!searchInput) return;
    
    // Function to show search suggestions
    const showSuggestions = () => {
        const searchTerm = searchInput.value.toLowerCase().trim();
        
        if (!suggestionsContainer) return;
        
        // Hide suggestions if search is empty
        if (searchTerm === '' || searchTerm.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        // Filter gigs based on search term
        const filteredGigs = allGigs.filter(gig => {
            const title = (gig.title || '').toLowerCase();
            const description = (gig.description || '').toLowerCase();
            const category = (gig.category || '').toLowerCase();
            const seller = (gig.seller_name || '').toLowerCase();
            
            return title.includes(searchTerm) ||
                   description.includes(searchTerm) ||
                   category.includes(searchTerm) ||
                   seller.includes(searchTerm);
        });
        
        // Show suggestions
        if (filteredGigs.length > 0) {
            const maxSuggestions = 5;
            const suggestions = filteredGigs.slice(0, maxSuggestions);
            
            suggestionsContainer.innerHTML = suggestions.map(gig => `
                <div class="search-suggestion-item" onclick="selectGig(${gig.id})">
                    <img src="${gig.image_url}" alt="${gig.title}" class="search-suggestion-image">
                    <div class="search-suggestion-content">
                        <h4 class="search-suggestion-title">${gig.title}</h4>
                        <div class="search-suggestion-meta">
                            <span class="search-suggestion-category">${gig.category} • by ${gig.seller_name}</span>
                            <span class="search-suggestion-price">${gig.price} Taka</span>
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Add footer if more results available
            if (filteredGigs.length > maxSuggestions) {
                suggestionsContainer.innerHTML += `
                    <div class="search-suggestions-footer">
                        +${filteredGigs.length - maxSuggestions} more results. Press Enter to view all.
                    </div>
                `;
            }
            
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.innerHTML = '<div class="search-suggestions-empty">No gigs found for "' + searchTerm + '"</div>';
            suggestionsContainer.style.display = 'block';
        }
    };
    
    // Function to perform full search
    const performSearch = () => {
        const searchTerm = searchInput.value.trim();
        
        // Hide suggestions
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
        
        // Reset pagination
        displayedGigsCount = 0;
        
        // Check if we're on the home page
        const container = document.querySelector('#gig-container');
        
        if (!container) {
            // If not on home page, redirect to home with search
            if (searchTerm) {
                window.location.href = `/?search=${encodeURIComponent(searchTerm)}`;
            } else {
                window.location.href = '/';
            }
            return;
        }
        
        // If search is empty, show all gigs
        if (searchTerm === '') {
            renderGigs(allGigs);
            return;
        }
        
        // Filter gigs based on search term (title, description, category, seller)
        const searchTermLower = searchTerm.toLowerCase();
        const filteredGigs = allGigs.filter(gig => {
            const title = (gig.title || '').toLowerCase();
            const description = (gig.description || '').toLowerCase();
            const category = (gig.category || '').toLowerCase();
            const seller = (gig.seller_name || '').toLowerCase();
            
            return title.includes(searchTermLower) ||
                   description.includes(searchTermLower) ||
                   category.includes(searchTermLower) ||
                   seller.includes(searchTermLower);
        });
        
        // Re-render with filtered results
        renderGigs(filteredGigs);
        
        // Scroll to results if found
        if (filteredGigs.length > 0) {
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };
    
    // Show suggestions on input
    searchInput.addEventListener('input', () => {
        showSuggestions();
        // Also perform live filtering if on home page
        const container = document.querySelector('#gig-container');
        if (container) {
            const searchTerm = searchInput.value.trim();
            if (searchTerm === '') {
                renderGigs(allGigs);
            } else {
                const searchTermLower = searchTerm.toLowerCase();
                const filteredGigs = allGigs.filter(gig => {
                    const title = (gig.title || '').toLowerCase();
                    const description = (gig.description || '').toLowerCase();
                    const category = (gig.category || '').toLowerCase();
                    const seller = (gig.seller_name || '').toLowerCase();
                    
                    return title.includes(searchTermLower) ||
                           description.includes(searchTermLower) ||
                           category.includes(searchTermLower) ||
                           seller.includes(searchTermLower);
                });
                renderGigs(filteredGigs);
            }
        }
    });
    
    // Search on Enter key
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
    
    // Search icon click
    const searchIcon = document.getElementById('search-icon');
    if (searchIcon) {
        searchIcon.style.pointerEvents = 'auto';
        searchIcon.style.cursor = 'pointer';
        searchIcon.addEventListener('click', () => {
            performSearch();
        });
    }
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (suggestionsContainer && !searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Show suggestions when focusing on input with existing text
    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim().length >= 2) {
            showSuggestions();
        }
    });
    
    // Check for search parameter in URL on page load
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('search');
    if (searchParam) {
        searchInput.value = searchParam;
        // Trigger search after gigs are loaded
        setTimeout(performSearch, 500);
    }
}

// Function to select a gig from suggestions
function selectGig(gigId) {
    // Redirect to gig detail page
    window.location.href = '/gig/' + gigId + '/';
}

// ========================================
// Order Handling with Modal
// ========================================
async function handleOrder(gigId) {
    const modal = document.querySelector('#order-modal');
    const modalContent = document.querySelector('#modal-content');
    
    if (!modal || !modalContent) {
        alert('Modal not found. Please refresh the page.');
        return;
    }
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Show loading spinner
    modalContent.innerHTML = `
        <h3>Processing Your Order...</h3>
        <div class="spinner"></div>
        <p>Please wait while we process your order.</p>
    `;
    
    // Simulate network delay (2 seconds)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    try {
        // Get CSRF token
        const csrftoken = getCookie('csrftoken');
        
        // Send POST request to Django
        const response = await fetch('/api/orders/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                gig_id: gigId,
                requirements: ''
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show success checkmark animation
            modalContent.innerHTML = `
                <h3>Order Placed Successfully!</h3>
                <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                    <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
                <p>Your order has been placed. Check your dashboard for updates.</p>
                <button class="btn btn-primary" onclick="closeModal()">Continue Shopping</button>
            `;
            
            // Update user balance in navbar
            updateBalanceDisplay(data.new_balance);
            
        } else {
            // Show error message
            modalContent.innerHTML = `
                <h3>Order Failed</h3>
                <p>${data.error}</p>
                <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            `;
        }
        
    } catch (error) {
        console.error('Error creating order:', error);
        modalContent.innerHTML = `
            <h3>Something Went Wrong</h3>
            <p>Unable to process your order. Please try again.</p>
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
        `;
    }
}

function closeModal() {
    const modal = document.querySelector('#order-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// ========================================
// User Balance Management
// ========================================
async function loadUserBalance() {
    try {
        const response = await fetch('/api/user/balance/');
        
        if (response.ok) {
            const data = await response.json();
            updateBalanceDisplay(data.balance);
        }
    } catch (error) {
        console.error('Error loading balance:', error);
    }
}

function updateBalanceDisplay(balance) {
    const balanceElement = document.querySelector('#user-balance');
    const balanceDropdown = document.querySelector('#user-balance-dropdown');
    
    console.log('Updating balance display:', balance);
    
    if (balanceElement) {
        balanceElement.textContent = balance.toFixed(2);
        
        // Add a brief animation
        balanceElement.style.transform = 'scale(1.2)';
        balanceElement.style.color = 'var(--gold)';
        
        setTimeout(() => {
            balanceElement.style.transform = 'scale(1)';
        }, 300);
    }

    // Update balance in profile dropdown
    if (balanceDropdown) {
        balanceDropdown.textContent = balance.toFixed(2);
        console.log('Dropdown balance updated to:', balance.toFixed(2));
    } else {
        console.warn('Balance dropdown element not found');
    }
}

// ========================================
// Dashboard Tab Switching
// ========================================
function setupDashboardTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    if (tabButtons.length === 0) return;
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetSection = button.getAttribute('data-target');
            
            // Remove active class from all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Hide all sections
            const sections = document.querySelectorAll('.dashboard-section');
            sections.forEach(section => {
                section.classList.remove('active');
            });
            
            // Show target section
            const target = document.querySelector(`#${targetSection}`);
            if (target) {
                target.classList.add('active');
            }
        });
    });
    
    // Setup filter tabs on home page
    const filterButtons = document.querySelectorAll('.tab-filter');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const filter = button.getAttribute('data-filter');
                
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                button.classList.add('active');
                
                // Load gigs with filter
                await loadGigsWithFilter(filter);
            });
        });
    }
}

// Helper function to update filter info display
function updateFilterInfo(category, filter, count) {
    const searchResultsInfo = document.getElementById('search-results-info');
    const searchResultsText = document.getElementById('search-results-text');
    
    if (!searchResultsInfo || !searchResultsText) return;
    
    let message = '';
    if (category) {
        message = `Showing ${count} gig${count !== 1 ? 's' : ''} in "${category}"`;
    } else if (filter === 'top-rated') {
        message = `Showing ${count} top-rated gig${count !== 1 ? 's' : ''}`;
    } else if (filter === 'new') {
        message = `Showing ${count} new gig${count !== 1 ? 's' : ''}`;
    }
    
    if (message) {
        searchResultsText.textContent = message;
        searchResultsInfo.style.display = 'block';
    } else {
        searchResultsInfo.style.display = 'none';
    }
}

// Load gigs with filter
async function loadGigsWithFilter(filter) {
    const container = document.querySelector('#gig-container');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading gigs...</div>';
    
    // Reset pagination
    displayedGigsCount = 0;
    
    try {
        const apiUrl = filter === 'all' ? '/api/gigs/' : `/api/gigs/?filter=${filter}`;
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error('Failed to fetch gigs');
        }
        
        const data = await response.json();
        allGigs = data.gigs;
        renderGigs(allGigs);
        updateFilterInfo(null, filter !== 'all' ? filter : null, allGigs.length);
    } catch (error) {
        console.error('Error loading gigs:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3>⚠️ Error Loading Gigs</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

// ========================================
// Load Buyer Orders
// ========================================
async function loadBuyerOrders() {
    const container = document.querySelector('#buyer-orders-container');
    
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading your orders...</div>';
    
    try {
        const response = await fetch('/api/orders/buyer/');
        
        if (!response.ok) {
            throw new Error('Failed to fetch orders');
        }
        
        const data = await response.json();
        
        if (data.orders.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No Orders Yet</h3>
                    <p>Browse gigs and place your first order!</p>
                </div>
            `;
            return;
        }
        
        // Render orders
        container.innerHTML = '';
        data.orders.forEach(order => {
            const orderCard = document.createElement('div');
            orderCard.className = 'glass-panel mb-20';
            orderCard.innerHTML = `
                <h4>${order.gig_title}</h4>
                <p>Seller: ${order.seller_name}</p>
                <p>Price: ${order.price} Taka</p>
                <p>Status: <span class="badge-${order.status}">${order.status}</span></p>
                <p>Ordered: ${new Date(order.created_at).toLocaleDateString()}</p>
                <a href="/order/${order.id}/" class="btn btn-primary" style="margin-top: 10px; display: inline-block;">View Details & Messages</a>
            `;
            container.appendChild(orderCard);
        });
        
    } catch (error) {
        console.error('Error loading buyer orders:', error);
        container.innerHTML = '<div class="empty-state"><h3>Error loading orders</h3></div>';
    }
}

// ========================================
// Load Seller Orders
// ========================================
async function loadSellerOrders() {
    const container = document.querySelector('#seller-orders-container');
    
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading your sales...</div>';
    
    try {
        const response = await fetch('/api/orders/seller/');
        
        if (!response.ok) {
            throw new Error('Failed to fetch orders');
        }
        
        const data = await response.json();
        
        if (data.orders.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No Sales Yet</h3>
                    <p>Create gigs to start selling!</p>
                </div>
            `;
            return;
        }
        
        // Render orders
        container.innerHTML = '';
        data.orders.forEach(order => {
            const orderCard = document.createElement('div');
            orderCard.className = 'glass-panel mb-20';
            orderCard.innerHTML = `
                <h4>${order.gig_title}</h4>
                <p>Buyer: ${order.buyer_name}</p>
                <p>Price: ${order.price} Taka</p>
                <p>Status: <span class="badge-${order.status}">${order.status}</span></p>
                <p>Requirements: ${order.requirements || 'None'}</p>
                <p>Ordered: ${new Date(order.created_at).toLocaleDateString()}</p>
                <a href="/order/${order.id}/" class="btn btn-primary" style="margin-top: 10px; display: inline-block;">View Details & Messages</a>
            `;
            container.appendChild(orderCard);
        });
        
    } catch (error) {
        console.error('Error loading seller orders:', error);
        container.innerHTML = '<div class="empty-state"><h3>Error loading sales</h3></div>';
    }
}

// ========================================
// Utility Functions
// ========================================

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ========================================
// Seller Earnings
// ========================================
async function loadSellerEarnings() {
    try {
        const response = await fetch('/api/seller/earnings/');
        
        if (response.ok) {
            const data = await response.json();
            
            // Update total earnings in profile dropdown
            const earningsElement = document.querySelector('#user-earnings');
            if (earningsElement) {
                earningsElement.textContent = data.total_earnings.toFixed(2);
            }
        }
    } catch (error) {
        console.error('Error loading earnings:', error);
    }
}

async function showEarningsModal(event) {
    event.preventDefault();
    
    const modal = document.querySelector('#earnings-modal');
    modal.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/seller/earnings/');
        const data = await response.json();
        
        // Update summary
        document.querySelector('#total-earnings').textContent = data.total_earnings.toFixed(2) + ' Taka';
        document.querySelector('#total-orders').textContent = data.total_orders;
        
        // Render earnings by gig
        const byGigContainer = document.querySelector('#earnings-by-gig');
        if (data.earnings_by_gig.length === 0) {
            byGigContainer.innerHTML = '<p style="text-align: center; color: #64748b; padding: 20px;">No earnings yet</p>';
        } else {
            byGigContainer.innerHTML = data.earnings_by_gig.map(item => `
                <div class="earnings-item">
                    <div class="earnings-item-info">
                        <div class="earnings-item-title">${item.gig_title}</div>
                        <div class="earnings-item-details">${item.orders_count} orders completed</div>
                    </div>
                    <div class="earnings-item-amount">${item.total_earned.toFixed(2)} Taka</div>
                </div>
            `).join('');
        }
        
        // Render recent earnings
        const recentContainer = document.querySelector('#recent-earnings');
        if (data.recent_earnings.length === 0) {
            recentContainer.innerHTML = '<p style="text-align: center; color: #64748b; padding: 20px;">No recent earnings</p>';
        } else {
            recentContainer.innerHTML = data.recent_earnings.map(item => `
                <div class="earnings-item">
                    <div class="earnings-item-info">
                        <div class="earnings-item-title">${item.gig_title}</div>
                        <div class="earnings-item-details">Order #${item.order_id} • ${item.buyer} • ${item.completed_at}</div>
                    </div>
                    <div class="earnings-item-amount">+${item.amount.toFixed(2)} Taka</div>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading earnings:', error);
    }
}

function closeEarningsModal() {
    document.querySelector('#earnings-modal').classList.add('hidden');
}

// Load seller's gigs
async function loadMyGigs() {
    const container = document.getElementById('my-gigs-container');
    
    try {
        const response = await fetch('/api/my-gigs/');
        const data = await response.json();
        
        if (data.gigs && data.gigs.length > 0) {
            container.innerHTML = `
                <div class="gigs-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px;">
                    ${data.gigs.map(gig => `
                        <div class="gig-card" style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s;">
                            <img src="${gig.image_url}" alt="${gig.title}" style="width: 100%; height: 180px; object-fit: cover;">
                            <div style="padding: 15px;">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                    <span style="display: inline-block; padding: 4px 10px; background: ${gig.status === 'active' ? '#10b981' : '#6b7280'}; color: white; border-radius: 12px; font-size: 0.8rem; text-transform: capitalize;">
                                        ${gig.status}
                                    </span>
                                    <span style="color: #64748b; font-size: 0.85rem;">${gig.created_at}</span>
                                </div>
                                <h3 style="font-size: 1rem; margin: 10px 0; color: var(--deep-blue);">${gig.title}</h3>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb;">
                                    <div>
                                        <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 4px;">${gig.category}</p>
                                        <p style="color: var(--gold); font-weight: bold; font-size: 1.1rem;">${gig.price} Taka</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <p style="color: #64748b; font-size: 0.85rem;">
                                            <i class="fas fa-clock"></i> ${gig.delivery_time} days
                                        </p>
                                    </div>
                                </div>
                                <div style="display: flex; gap: 8px; margin-top: 12px;">
                                    <button onclick="window.location.href='/update-gig/${gig.id}/'" class="btn btn-secondary" style="flex: 1; padding: 8px; font-size: 0.9rem;">
                                        <i class="fas fa-edit"></i> Edit
                                    </button>
                                    <button onclick="viewGig(${gig.id})" class="btn btn-primary" style="flex: 1; padding: 8px; font-size: 0.9rem;">
                                        <i class="fas fa-eye"></i> View
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #64748b;">
                    <i class="fas fa-briefcase" style="font-size: 3rem; margin-bottom: 15px; opacity: 0.3;"></i>
                    <p style="font-size: 1.1rem; margin-bottom: 10px;">You haven't created any gigs yet</p>
                    <p style="font-size: 0.95rem;">Create your first gig to start selling your services!</p>
                    <a href="/create-gig/" class="btn btn-primary" style="margin-top: 20px; display: inline-block;">
                        <i class="fas fa-plus"></i> Create Your First Gig
                    </a>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading gigs:', error);
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ef4444;">
                <p>Error loading gigs. Please try again later.</p>
            </div>
        `;
    }
}

// View gig details
function viewGig(gigId) {
    window.location.href = `/gig/${gigId}/`;
}

// Load conversations for messages dropdown
let currentMessageOrderId = null;

async function loadConversations() {
    const container = document.getElementById('conversations-list');
    const badge = document.getElementById('messages-badge');
    
    try {
        const response = await fetch('/api/conversations/');
        const data = await response.json();
        
        // Update badge
        if (data.total_unread > 0) {
            badge.textContent = data.total_unread;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
        
        if (data.conversations && data.conversations.length > 0) {
            container.innerHTML = data.conversations.map(conv => {
                const timeAgo = getTimeAgo(new Date(conv.last_message_time));
                return `
                    <div class="conversation-item ${conv.unread_count > 0 ? 'unread' : ''}" onclick="window.location.href='/order/${conv.order_id}/'">
                        <div class="conversation-avatar">${conv.other_user.charAt(0).toUpperCase()}</div>
                        <div class="conversation-content">
                            <div class="conversation-header">
                                <span class="conversation-user">${conv.other_user}</span>
                                <span class="conversation-time">${timeAgo}</span>
                            </div>
                            <div class="conversation-gig">${conv.gig_title}</div>
                            <div class="conversation-last-message">
                                ${conv.last_message}
                                ${conv.unread_count > 0 ? `<span class="conversation-unread">${conv.unread_count}</span>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="empty-conversations">
                    <i class="fas fa-comments"></i>
                    <p>No messages yet</p>
                    <p style="font-size: 0.85rem;">Start a conversation by placing an order</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #ef4444;">Error loading conversations</div>';
    }
}

// Open messages modal
async function openMessagesModal(orderId) {
    currentMessageOrderId = orderId;
    const modal = document.getElementById('messages-modal');
    modal.style.display = 'flex';
    
    await loadMessagesForOrder(orderId);
}

// Close messages modal
function closeMessagesModal() {
    const modal = document.getElementById('messages-modal');
    modal.style.display = 'none';
    currentMessageOrderId = null;
    
    // Reload conversations to update unread counts
    loadConversations();
}

// Load messages for a specific order
async function loadMessagesForOrder(orderId) {
    const container = document.getElementById('messages-container');
    const orderInfo = document.getElementById('messages-order-info');
    const title = document.getElementById('messages-modal-title');
    
    container.innerHTML = '<div class="loading" style="text-align: center; padding: 20px;">Loading messages...</div>';
    
    try {
        const response = await fetch(`/api/orders/${orderId}/messages/`);
        const data = await response.json();
        
        if (data.order_info) {
            title.textContent = data.order_info.gig_title;
            orderInfo.innerHTML = `
                <div class="order-info-left">
                    <h3>${data.order_info.gig_title}</h3>
                    <p><strong>With:</strong> ${data.order_info.other_user}</p>
                    <p><strong>Price:</strong> ${data.order_info.price} Taka</p>
                </div>
                <span class="order-status-badge status-${data.order_info.status}">${data.order_info.status.replace('_', ' ')}</span>
            `;
        }
        
        if (data.messages && data.messages.length > 0) {
            container.innerHTML = data.messages.map(msg => {
                const time = new Date(msg.created_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                });
                return `
                    <div class="message-bubble ${msg.is_own ? 'own' : 'other'}">
                        <span class="message-sender">${msg.sender}</span>
                        <div class="message-content">${msg.message}</div>
                        <span class="message-time">${time}</span>
                    </div>
                `;
            }).join('');
            
            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
        } else {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: #94a3b8;">No messages yet. Start the conversation!</div>';
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: #ef4444;">Error loading messages</div>';
    }
}

// Send message from modal
async function sendMessageFromModal() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message || !currentMessageOrderId) return;
    
    try {
        const response = await fetch(`/api/orders/${currentMessageOrderId}/send-message/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            input.value = '';
            await loadMessagesForOrder(currentMessageOrderId);
        } else {
            alert('Error sending message: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Error sending message. Please try again.');
    }
}

// Load notifications
async function loadNotifications() {
    const container = document.getElementById('notifications-list');
    const badge = document.getElementById('notifications-badge');
    
    try {
        const response = await fetch('/api/notifications/');
        const data = await response.json();
        
        // Update badge
        if (data.unread_count > 0) {
            badge.textContent = data.unread_count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
        
        if (data.notifications && data.notifications.length > 0) {
            container.innerHTML = data.notifications.map(notif => {
                const timeAgo = getTimeAgo(new Date(notif.created_at));
                const icon = getNotificationIcon(notif.type);
                const clickable = notif.order_id ? 'clickable' : '';
                const unread = !notif.is_read ? 'unread' : '';
                
                return `
                    <div class="notification-item ${clickable} ${unread}" 
                         ${notif.order_id ? `onclick="handleNotificationClick(${notif.id}, ${notif.order_id})"` : `onclick="markNotificationRead(${notif.id})"`}>
                        <div class="notification-icon">${icon}</div>
                        <div class="notification-content">
                            <div class="notification-title">${notif.title}</div>
                            <div class="notification-time">${timeAgo}</div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="empty-conversations">
                    <i class="fas fa-bell-slash"></i>
                    <p>No notifications yet</p>
                    <p style="font-size: 0.85rem;">We'll notify you when something happens</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #ef4444;">Error loading notifications</div>';
    }
}

// Get notification icon based on type
function getNotificationIcon(type) {
    const icons = {
        'order_placed': '📦',
        'order_accepted': '✅',
        'order_delivered': '🚚',
        'order_completed': '🎉',
        'order_cancelled': '❌',
        'message_received': '💬',
        'review_received': '⭐'
    };
    return icons[type] || '📢';
}

// Handle notification click
async function handleNotificationClick(notificationId, orderId) {
    await markNotificationRead(notificationId);
    if (orderId) {
        openMessagesModal(orderId);
    }
}

// Mark notification as read
async function markNotificationRead(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        loadNotifications();
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Mark all notifications as read
async function markAllNotificationsRead() {
    try {
        await fetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        loadNotifications();
    } catch (error) {
        console.error('Error marking all notifications as read:', error);
    }
}

// Helper function to get time ago
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + 'd ago';
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Export functions for global access
window.handleOrder = handleOrder;
window.closeModal = closeModal;
window.loadGigs = loadGigs;
window.loadBuyerOrders = loadBuyerOrders;
window.loadSellerOrders = loadSellerOrders;
window.showEarningsModal = showEarningsModal;
window.closeEarningsModal = closeEarningsModal;
window.loadMyGigs = loadMyGigs;
window.loadConversations = loadConversations;
window.openMessagesModal = openMessagesModal;
window.closeMessagesModal = closeMessagesModal;
window.sendMessageFromModal = sendMessageFromModal;
window.loadNotifications = loadNotifications;
window.markNotificationRead = markNotificationRead;
window.markAllNotificationsRead = markAllNotificationsRead;
window.handleNotificationClick = handleNotificationClick;

// Clear search function
function clearSearch() {
    const searchInput = document.querySelector('#search-input');
    const suggestionsContainer = document.getElementById('search-suggestions');
    if (searchInput) {
        searchInput.value = '';
        renderGigs(allGigs);
        searchInput.focus();
    }
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}
window.clearSearch = clearSearch;
window.selectGig = selectGig;


// ========================================
// Balance Request Functions
// ========================================
async function showBalanceRequestModal(event) {
    if (event) event.preventDefault();
    
    const modal = document.getElementById('balance-request-modal');
    modal.classList.remove('hidden');
    
    // Reset form
    document.getElementById('balance-request-form').reset();
    
    // Reload current balance
    await loadUserBalance();
    
    // Load existing requests
    await loadBalanceRequests();
}

function closeBalanceRequestModal() {
    const modal = document.getElementById('balance-request-modal');
    modal.classList.add('hidden');
}

async function submitBalanceRequest(event) {
    event.preventDefault();
    
    const amount = document.getElementById('balance-amount').value;
    const note = document.getElementById('balance-note').value;
    
    try {
        const response = await fetch('/api/balance-request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                amount: parseFloat(amount),
                note: note
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Balance request submitted successfully! Admin will review your request.');
            document.getElementById('balance-request-form').reset();
            await loadBalanceRequests();
            await loadUserBalance();
        } else {
            alert('Error: ' + (data.error || 'Failed to submit request'));
        }
    } catch (error) {
        console.error('Error submitting balance request:', error);
        alert('Failed to submit balance request. Please try again.');
    }
}

async function loadBalanceRequests() {
    const container = document.getElementById('balance-requests-list');
    
    try {
        const response = await fetch('/api/balance-requests/');
        const data = await response.json();
        
        // Reload balance to show any updates from approved requests
        await loadUserBalance();
        
        if (data.requests.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No balance requests yet</p>';
            return;
        }
        
        container.innerHTML = data.requests.map(req => {
            const statusColor = req.status === 'approved' ? '#10b981' : 
                              req.status === 'rejected' ? '#ef4444' : '#f59e0b';
            const statusIcon = req.status === 'approved' ? '✓' : 
                             req.status === 'rejected' ? '✗' : '⏳';
            
            return `
                <div style="padding: 15px; margin-bottom: 10px; background: #f8fafc; border-radius: 8px; border-left: 4px solid ${statusColor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: var(--deep-blue);">
                            ${req.amount} Taka
                        </div>
                        <div style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;">
                            ${statusIcon} ${req.status.toUpperCase()}
                        </div>
                    </div>
                    ${req.note ? `<div style="color: #64748b; font-size: 0.9rem; margin-bottom: 8px;">${req.note}</div>` : ''}
                    ${req.admin_note ? `<div style="color: #64748b; font-size: 0.85rem; font-style: italic; margin-bottom: 8px;">Admin: ${req.admin_note}</div>` : ''}
                    <div style="color: #94a3b8; font-size: 0.85rem;">
                        ${req.created_at}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading balance requests:', error);
        container.innerHTML = '<p style="text-align: center; color: #ef4444;">Failed to load requests</p>';
    }
}

// Expose functions to window
window.showBalanceRequestModal = showBalanceRequestModal;
window.closeBalanceRequestModal = closeBalanceRequestModal;
window.submitBalanceRequest = submitBalanceRequest;
window.loadBalanceRequests = loadBalanceRequests;


// ========================================
// Cashout Request Functions
// ========================================
async function showCashoutModal(event) {
    if (event) event.preventDefault();
    
    const modal = document.getElementById('cashout-modal');
    modal.classList.remove('hidden');
    
    // Reset form
    document.getElementById('cashout-form').reset();
    
    // Load available earnings
    await loadAvailableEarnings();
    
    // Load existing requests
    await loadCashoutRequests();
}

function closeCashoutModal() {
    const modal = document.getElementById('cashout-modal');
    modal.classList.add('hidden');
}

async function loadAvailableEarnings() {
    try {
        const response = await fetch('/api/available-earnings/');
        const data = await response.json();
        
        document.getElementById('total-earnings-display').textContent = data.total_earnings.toFixed(2) + ' Taka';
        document.getElementById('cashed-out-display').textContent = data.total_cashed_out.toFixed(2) + ' Taka';
        document.getElementById('available-earnings-display').textContent = data.available_earnings.toFixed(2) + ' Taka';
        
        // Update max attribute on amount input
        const amountInput = document.getElementById('cashout-amount');
        amountInput.max = data.available_earnings;
        
    } catch (error) {
        console.error('Error loading available earnings:', error);
    }
}

async function submitCashoutRequest(event) {
    event.preventDefault();
    
    const amount = parseFloat(document.getElementById('cashout-amount').value);
    const paymentMethod = document.getElementById('payment-method').value;
    const paymentDetails = document.getElementById('payment-details').value;
    const note = document.getElementById('cashout-note').value;
    
    try {
        const response = await fetch('/api/cashout-request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                amount: amount,
                payment_method: paymentMethod,
                payment_details: paymentDetails,
                note: note
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Cashout request submitted successfully! Admin will process your payment.');
            document.getElementById('cashout-form').reset();
            await loadAvailableEarnings();
            await loadCashoutRequests();
            await loadSellerEarnings(); // Refresh earnings display
        } else {
            alert('Error: ' + (data.error || 'Failed to submit request'));
        }
    } catch (error) {
        console.error('Error submitting cashout request:', error);
        alert('Failed to submit cashout request. Please try again.');
    }
}

async function loadCashoutRequests() {
    const container = document.getElementById('cashout-requests-list');
    
    try {
        const response = await fetch('/api/cashout-requests/');
        const data = await response.json();
        
        if (data.requests.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No cashout requests yet</p>';
            return;
        }
        
        container.innerHTML = data.requests.map(req => {
            const statusColor = req.status === 'approved' ? '#10b981' : 
                              req.status === 'rejected' ? '#ef4444' : '#f59e0b';
            const statusIcon = req.status === 'approved' ? '✓' : 
                             req.status === 'rejected' ? '✗' : '⏳';
            
            return `
                <div style="padding: 15px; margin-bottom: 10px; background: #f8fafc; border-radius: 8px; border-left: 4px solid ${statusColor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: var(--deep-blue);">
                            ${req.amount} Taka via ${req.payment_method}
                        </div>
                        <div style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;">
                            ${statusIcon} ${req.status.toUpperCase()}
                        </div>
                    </div>
                    <div style="color: #64748b; font-size: 0.9rem; margin-bottom: 4px;">
                        ${req.payment_details}
                    </div>
                    ${req.note ? `<div style="color: #64748b; font-size: 0.9rem; margin-bottom: 8px;">Note: ${req.note}</div>` : ''}
                    ${req.admin_note ? `<div style="color: #64748b; font-size: 0.85rem; font-style: italic; margin-bottom: 8px;">Admin: ${req.admin_note}</div>` : ''}
                    <div style="color: #94a3b8; font-size: 0.85rem;">
                        ${req.created_at}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading cashout requests:', error);
        container.innerHTML = '<p style="text-align: center; color: #ef4444;">Failed to load requests</p>';
    }
}

// Expose functions to window
window.showCashoutModal = showCashoutModal;
window.closeCashoutModal = closeCashoutModal;
window.submitCashoutRequest = submitCashoutRequest;
window.loadCashoutRequests = loadCashoutRequests;
window.loadAvailableEarnings = loadAvailableEarnings;


// ========================================
// Cashout History Functions
// ========================================
async function showCashoutHistoryModal(event) {
    if (event) event.preventDefault();
    
    const modal = document.getElementById('cashout-history-modal');
    modal.classList.remove('hidden');
    
    // Load earnings summary and history
    await loadCashoutHistory();
}

function closeCashoutHistoryModal() {
    const modal = document.getElementById('cashout-history-modal');
    modal.classList.add('hidden');
}

async function loadCashoutHistory() {
    try {
        // Load earnings summary
        const earningsResponse = await fetch('/api/available-earnings/');
        const earningsData = await earningsResponse.json();
        
        document.getElementById('history-total-earnings').textContent = earningsData.total_earnings.toFixed(2) + ' Taka';
        document.getElementById('history-cashed-out').textContent = earningsData.total_cashed_out.toFixed(2) + ' Taka';
        document.getElementById('history-available').textContent = earningsData.available_earnings.toFixed(2) + ' Taka';
        
        // Load approved cashout history
        const historyResponse = await fetch('/api/cashout-requests/');
        const historyData = await historyResponse.json();
        
        const container = document.getElementById('cashout-history-list');
        
        // Filter only approved requests
        const approvedRequests = historyData.requests.filter(req => req.status === 'approved');
        
        if (approvedRequests.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No cashout history yet</p>';
            return;
        }
        
        container.innerHTML = approvedRequests.map(req => {
            return `
                <div style="padding: 15px; margin-bottom: 10px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #10b981;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: var(--deep-blue); font-size: 1.1rem;">
                            ${req.amount} Taka
                        </div>
                        <div style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;">
                            ✓ PAID
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 8px;">
                        <div>
                            <div style="color: #64748b; font-size: 0.85rem;">Payment Method</div>
                            <div style="color: var(--deep-blue); font-weight: 600;">${req.payment_method}</div>
                        </div>
                        <div>
                            <div style="color: #64748b; font-size: 0.85rem;">Account</div>
                            <div style="color: var(--deep-blue); font-weight: 600;">${req.payment_details}</div>
                        </div>
                    </div>
                    ${req.admin_note ? `<div style="color: #059669; font-size: 0.9rem; background: white; padding: 8px; border-radius: 4px; margin-bottom: 8px;">
                        <strong>Admin:</strong> ${req.admin_note}
                    </div>` : ''}
                    <div style="color: #94a3b8; font-size: 0.85rem;">
                        Processed on ${req.updated_at}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading cashout history:', error);
        document.getElementById('cashout-history-list').innerHTML = '<p style="text-align: center; color: #ef4444;">Failed to load history</p>';
    }
}

// Expose functions to window
window.showCashoutHistoryModal = showCashoutHistoryModal;
window.closeCashoutHistoryModal = closeCashoutHistoryModal;
window.loadCashoutHistory = loadCashoutHistory;
