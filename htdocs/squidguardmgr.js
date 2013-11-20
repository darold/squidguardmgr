function validate_schedule ()
{
	if (document.forms[0].time.value == '') {
		alert('You must give a rule name');
		return false;
	}
	// Starting+Ending time is optional
	if ( (document.forms[0].starthour.selectedIndex > 0) || (document.forms[0].startmin.selectedIndex > 0) || (document.forms[0].endhour.selectedIndex > 0) || (document.forms[0].endmin.selectedIndex > 0) ) {
		if (document.forms[0].starthour.selectedIndex == 0) {
			alert('You must select a starting hour');
			return false;
		}
		if (document.forms[0].startmin.selectedIndex == 0) {
			alert('You must select a starting minute');
			return false;
		}
		if (document.forms[0].endhour.selectedIndex == 0) {
			alert('You must select an ending hour');
			return false;
		}
		if (document.forms[0].endmin.selectedIndex == 0) {
			alert('You must select an ending minute');
			return false;
		}
	}
	var daychecked = 0;
	for (var i = 0; i < document.forms[0].week.length; i++) {
		if (document.forms[0].week[i].checked == true) {
			daychecked = 1;
			break;
		}
	}
	if (document.forms[0].date.value == '') {
		if (daychecked == 0) {
			alert('You must select a weekday or a date');
			return false;
		}
	}
	if (document.forms[0].date.value != '') {
		if (daychecked != 0) {
			alert('You must choose between a weekday or a date, not both');
			return false;
		}
	}

	return true;
}

function validate_source ()
{
	if (document.forms[0].src.value == '') {
		alert('You must give a rule name');
		return false;
	}
	if (document.forms[0].srctype.selectedIndex == 0) {
		alert('You must select a type of source');
		return false;
	}
	if (document.forms[0].srcval.value == '') {
		alert('You must give a value for the type of source');
		return false;
	}

	return true;
}

function validate_rewrite ()
{
	if (document.forms[0].rewrite.value == '') {
		alert('You must give a rule name');
		return false;
	}
	if (document.forms[0].pattern == undefined) {
		if (document.forms[0].srcval.value == '') {
			alert('You must give a value');
			return false;
		}
	} else {
		if (document.forms[0].pattern.value == '') {
			alert('You must give a pattern to replace');
			return false;
		}
		if (document.forms[0].substitute.value == '') {
			alert('You must give a substitution for replacement');
			return false;
		}
	}

	return true;
}

function validate_filter ()
{
	if (document.forms[0].category.value == '') {
		alert('You must give a rule name');
		return false;
	}
	if ( (document.forms[0].domainlist.selectedIndex == 0) && (document.forms[0].urllist.selectedIndex == 0) && (document.forms[0].expressionlist.selectedIndex == 0) ) {
		alert('You must select a domains and/or urls and/or expressions list');
		return false;
	}

	return true;
}

function validate_policy ()
{
	if (document.forms[0].acl.value == '') {
		alert('You must select a source');
		return false;
	}
	var destchecked = 0;
	for (var i = 0; i < document.forms[0].dest.length; i++) {
		if (document.forms[0].dest[i].checked == true) {
			destchecked = 1;
			break;
		}
	}

	if (destchecked == 0) {
		alert('You must set a destination to apply a filter');
		return false;
	}

	if ( (document.forms[0].log.value != '') && (document.forms[0].redirect.value == '') ) {
		alert('You must set a redirection URL');
		return false;
	}
	return true;
}

function conditional_status (idx) 
{
	if (idx == 0) {
		for (var i = 0; i < document.forms[0].elements.length; i++) {
			if (document.forms[0].elements[i].name == 'edest') {
				document.forms[0].elements[i].disabled = true;
			}
			if (document.forms[0].elements[i].name == 'erew') {
				document.forms[0].elements[i].disabled = true;
			}
			if (document.forms[0].elements[i].name == 'eredirect') {
				document.forms[0].elements[i].disabled = true;
			}
			if (document.forms[0].elements[i].name == 'elog') {
				document.forms[0].elements[i].disabled = true;
			}
		}
	} else {
		for (var i = 0; i < document.forms[0].elements.length; i++) {
			if (document.forms[0].elements[i].name == 'edest') {
				document.forms[0].elements[i].disabled = false;
			}
			if (document.forms[0].elements[i].name == 'erew') {
				document.forms[0].elements[i].disabled = false;
			}
			if (document.forms[0].elements[i].name == 'eredirect') {
				document.forms[0].elements[i].disabled = false;
			}
			if (document.forms[0].elements[i].name == 'elog') {
				document.forms[0].elements[i].disabled = false;
			}
		}
	}
}

function pick_redirect ()
{
	var str = '';
	var radioList = document.forms[0].redirect;
	for (var i=0; i<radioList.length; i++) {
		if (radioList[i].checked) {
			str = radioList[i].value;
			break;
		}
	}
	return str;
}
