/* ═══════════════════════════════════════════════════════
   CINEFILE — base.js
   Shared behaviour for every page:
     1. Mobile side-menu + search-toggle
     2. Carousel arrow helpers
     3. Watch-toggle buttons (grid cards)
     3b. Watch / watchlist buttons (movie detail page)
     4. bfcache (back/forward cache) sync
   ═══════════════════════════════════════════════════════ */

/* ──────────────────────────────────────────────────────
   1. MOBILE NAV — side menu + search row
   ────────────────────────────────────────────────────── */
(function () {
    var menuToggle    = document.getElementById('menuToggle');
    var sideMenu      = document.getElementById('sideMenu');
    var sideMenuClose = document.getElementById('sideMenuClose');
    var scrim         = document.getElementById('navScrim');
    var searchToggle  = document.getElementById('mobileSearchToggle');
    var searchRow     = document.getElementById('mobileSearchRow');

    if (!menuToggle) return; // nav not present on this page

    function openMenu() {
        sideMenu.classList.add('open');
        scrim.classList.add('open');
        sideMenu.setAttribute('aria-hidden', 'false');
        menuToggle.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        sideMenu.classList.remove('open');
        scrim.classList.remove('open');
        sideMenu.setAttribute('aria-hidden', 'true');
        menuToggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }

    menuToggle.addEventListener('click', openMenu);
    sideMenuClose.addEventListener('click', closeMenu);
    scrim.addEventListener('click', closeMenu);

    if (searchToggle && searchRow) {
        searchToggle.addEventListener('click', function () {
            var isOpen = searchRow.classList.toggle('open');
            searchToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            if (isOpen) {
                var inp = searchRow.querySelector('input');
                if (inp) inp.focus();
            }
        });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeMenu();
            if (searchRow) {
                searchRow.classList.remove('open');
                if (searchToggle) searchToggle.setAttribute('aria-expanded', 'false');
            }
        }
    });
})();

/* ──────────────────────────────────────────────────────
   2. CAROUSEL helpers
   Used on watched_list, watched_movies_all, watched_franchises_all.
   Safe to include everywhere — no-ops if no carousels exist.
   ────────────────────────────────────────────────────── */
function scrollCarousel(button, direction) {
    var wrap  = button.closest('.carousel-wrap');
    var track = wrap.querySelector('.carousel-track');
    track.scrollBy({ left: direction * track.clientWidth * 0.85, behavior: 'smooth' });
}

function updateArrowVisibility(track) {
    var wrap  = track.closest('.carousel-wrap');
    var left  = wrap.querySelector('.carousel-arrow.left');
    var right = wrap.querySelector('.carousel-arrow.right');
    if (!left || !right) return;
    left.classList.toggle('is-hidden',  track.scrollLeft <= 5);
    right.classList.toggle('is-hidden', track.scrollLeft + track.clientWidth >= track.scrollWidth - 5);
}

document.querySelectorAll('.carousel-track').forEach(function (track) {
    updateArrowVisibility(track);
    track.addEventListener('scroll', function () { updateArrowVisibility(track); });
});

window.addEventListener('resize', function () {
    document.querySelectorAll('.carousel-track').forEach(updateArrowVisibility);
});

/* ──────────────────────────────────────────────────────
   3. WATCH-TOGGLE buttons (poster / grid cards)
   Toggles the .watched class on a card and syncs the
   change to the server. Safe no-op if no buttons exist.
   ────────────────────────────────────────────────────── */
(function () {
    function getCookie(name) {
        var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return match ? match.pop() : '';
    }
    var csrftoken = getCookie('csrftoken');

    document.querySelectorAll('.watch-toggle-btn').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            var movieId = this.getAttribute('data-movie-id');
            var cardElement = document.getElementById('card-' + movieId);
            var isCurrentlyWatched = cardElement.classList.contains('watched');

            if (isCurrentlyWatched) cardElement.classList.remove('watched');
            else cardElement.classList.add('watched');

            fetch('/toggle/' + movieId + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' }
            })
            .then(function (res) {
                if (res.status === 403 || res.redirected) throw new Error('auth');
                if (!res.ok) throw new Error('network');
                return res.json();
            })
            .catch(function (err) {
                if (isCurrentlyWatched) cardElement.classList.add('watched');
                else cardElement.classList.remove('watched');

                if (err.message === 'auth') {
                    alert('Please log in to track watched movies.');
                } else {
                    alert('Connection error. Could not save progress.');
                }
            });
        });
    });
})();

/* ──────────────────────────────────────────────────────
   3b. WATCH / WATCHLIST buttons (movie detail page)
   Standalone buttons, no card wrapper — toggle classes
   and label text directly on the button itself.
   ────────────────────────────────────────────────────── */
(function () {
    function getCookie(name) {
        var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return match ? match.pop() : '';
    }
    var csrftoken = getCookie('csrftoken');

    var watchBtn = document.getElementById('watch-btn');
    if (watchBtn) {
        watchBtn.addEventListener('click', function () {
            var movieId = watchBtn.getAttribute('data-movie-id');
            if (!movieId) {
                console.error('watch-btn is missing data-movie-id');
                return;
            }
            var wasWatched = watchBtn.classList.contains('btn-watched');

            function applyState(watched) {
                watchBtn.classList.toggle('btn-watched', watched);
                watchBtn.classList.toggle('btn-unwatched', !watched);
                watchBtn.textContent = watched ? '✓ Watched' : '+ Mark as Watched';
            }

            applyState(!wasWatched);

            fetch('/toggle/' + movieId + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' }
            })
            .then(function (res) {
                if (res.status === 403 || res.redirected) throw new Error('auth');
                if (!res.ok) throw new Error('network');
                return res.json();
            })
            .catch(function (err) {
                applyState(wasWatched);
                if (err.message === 'auth') {
                    alert('Please log in to track watched movies.');
                } else {
                    alert('Connection error. Could not save progress.');
                }
            });
        });
    }

    var watchlistBtn = document.getElementById('watchlist-btn');
    if (watchlistBtn) {
        watchlistBtn.addEventListener('click', function () {
            var movieId = watchlistBtn.getAttribute('data-movie-id');
            if (!movieId) {
                console.error('watchlist-btn is missing data-movie-id');
                return;
            }
            var wasInWatchlist = watchlistBtn.classList.contains('btn-watchlist-added');

            function applyState(inWatchlist) {
                watchlistBtn.classList.toggle('btn-watchlist-added', inWatchlist);
                watchlistBtn.classList.toggle('btn-watchlist-add', !inWatchlist);
                watchlistBtn.textContent = inWatchlist ? '✓ In Watchlist' : '+ Add to Watchlist';
            }

            applyState(!wasInWatchlist);

            fetch('/toggle-watchlist/' + movieId + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' }
            })
            .then(function (res) {
                if (res.status === 403 || res.redirected) throw new Error('auth');
                if (!res.ok) throw new Error('network');
                return res.json();
            })
            .catch(function (err) {
                applyState(wasInWatchlist);
                if (err.message === 'auth') {
                    alert('Please log in to track your watchlist.');
                } else {
                    alert('Connection error. Could not save progress.');
                }
            });
        });
    }
})();

/* ──────────────────────────────────────────────────────
   4. BFCACHE SYNC
   When a page is restored from the back/forward cache,
   re-fetch watched status so toggles reflect the latest
   state instead of a stale snapshot.
   ────────────────────────────────────────────────────── */
window.addEventListener('pageshow', function (event) {
    if (!event.persisted) return; // Only act when page is restored from bfcache

    var buttons = document.querySelectorAll('.watch-toggle-btn');
    if (buttons.length === 0) return;

    var ids = Array.from(buttons).map(function (btn) { return btn.dataset.movieId; }).join(',');

    fetch('/watched-status/?ids=' + ids)
        .then(function (res) { return res.json(); })
        .then(function (data) {
            var watchedSet = new Set(data.watched.map(String));
            buttons.forEach(function (btn) {
                var movieId = String(btn.dataset.movieId);
                var cardElement = document.getElementById('card-' + movieId);
                if (watchedSet.has(movieId)) {
                    cardElement.classList.add('watched');
                } else {
                    cardElement.classList.remove('watched');
                }
            });
        })
        .catch(function (error) { console.error('Failed to sync watched status:', error); });
});