function onThemeToggled(e) {
	if (typeof Storage !== 'undefined') {
		if (e.currentTarget.checked === true) {
			localStorage.setItem(
				'switchedThemeFromDefault',
				'true'
			);
		} else {
			localStorage.removeItem(
				'switchedThemeFromDefault'
			);
		}
	} else {
		console.log(
			'No storage supported!' +
			'Theme selection wont be saved!'
		);
	}
}

document.addEventListener('DOMContentLoaded', function(event) {
	if (typeof Storage !== 'undefined') {
		var themeToggler = document.querySelector('#theme-toggler');
		themeToggler.checked =
			localStorage.getItem('switchedThemeFromDefault') === 'true';
	} else {
		console.log(
			'No storage supported!' +
			'Theme selection wont be saved!'
		);
	}

	document.querySelectorAll('pre code').forEach(function(block) {
		hljs.highlightBlock(block);
	});
});

