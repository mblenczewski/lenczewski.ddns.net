document.addEventListener('DOMContentLoaded',function(e){
	const themeToggler = document.querySelector('#theme-toggler');
	const themeCookie = 'switchedThemeFromDefault';

	if (typeof Storage !== 'undefined') {
		themeToggler.checked = localStorage.getItem(themeCookie) === 'true';
	} else {
		console.log('No storage supported! Theme selection wont be saved!');
	}

	themeToggler.addEventListener('change',function(e){
		if (typeof Storage !== 'undefined') {
			if (e.currentTarget.checked === true) {
				localStorage.setItem(themeCookie,'true');
			} else {
				localStorage.removeItem(themeCookie);
			}
		} else {
			console.log('No storage supported! Theme selection wont be saved!');
		}
	});

	document.querySelectorAll('pre code').forEach(function(block){
		hljs.highlightBlock(block);
	});
});

