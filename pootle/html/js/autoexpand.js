var W3CDOM = (document.createElement && document.getElementsByTagName);

window.onload = init;

function init()
{
	if (!W3CDOM) return;
	var divs = document.getElementsByTagName('div');
	for (var i=0;i<divs.length;i++)
	{
		if (divs[i].className.indexOf('autoexpand') != -1)
		{
			var divobj = divs[i];
			if (divobj.id.match("orig[0-9]+"))
			{
				divobj.rownum = parseInt(divobj.id.replace("orig", ""));
				divobj.partner = document.getElementById("trans"+divobj.rownum)
			}
			else if (divobj.id.match("trans[0-9]+"))
			{
				divobj.rownum = parseInt(divobj.id.replace("trans", ""));
				divobj.partner = document.getElementById("orig"+divobj.rownum)
			}
			else
			{
				divobj.rownum = -1;
			}
			divobj.contractedHeight = 50;
			divobj.expandedHeight = 999;
			divobj.makeexpanded = makeexpanded;
			divobj.makecontracted = makecontracted;
			divobj.expandaction = expandaction;
			divobj.contractaction = contractaction;
			divobj.autoexpandstate = 'mouse';
			divobj.onmouseover = mouseGoesOver;
			divobj.onmouseout = mouseGoesOut;
			divobj.onclick = mouseClick;
			divobj.makecontracted();
		}
	}
}

function makeexpanded()
{
	this.style.maxHeight = this.expandedHeight + 'px';
	if (this.offsetHeight >= this.expandedHeight)
		this.style.borderBottom = '1px dotted #999';
	else
		this.style.borderBottom = '0';
}

function makecontracted()
{
	this.style.maxHeight = this.contractedHeight + 'px';
	if (this.offsetHeight >= this.contractedHeight)
		this.style.borderBottom = '1px dotted #999';
	else
		this.style.borderBottom = '0';
}

function expandaction()
{
	if (this.autoexpandstate == 'mouse')
	{
		this.makeexpanded();
		if (this.partner)
		{
			this.partner.makeexpanded();
		}
	}
}

function contractaction()
{
	if (this.autoexpandstate == 'mouse')
	{
		this.makecontracted();
		if (this.partner)
		{
			this.partner.makecontracted();
		}
	}
}

function timedexpansion(divid)
{
	var div = document.getElementById(divid);
	div.expandaction();
}

function timedcontraction(divid)
{
	var div = document.getElementById(divid);
	div.contractaction();
}

function mouseGoesOver()
{
	if (this.timeevent)
		clearTimeout(this.timeevent);
	if (this.partner)
		if (this.partner.timeevent)
			clearTimeout(this.partner.timeevent);
	this.timeevent = setTimeout('timedexpansion("'+this.id+'")', 300);
}

function mouseGoesOut()
{
	if (this.timeevent)
		clearTimeout(this.timeevent);
	if (this.partner)
		if (this.partner.timeevent)
			clearTimeout(this.partner.timeevent);
	this.timeevent = setTimeout('timedcontraction("'+this.id+'")', 300);
}

function mouseClick()
{
	if (this.autoexpandstate == 'mouse')
	{
		this.autoexpandstate = 'seton';
		this.makeexpanded();
		if (this.partner)
		{
			this.partner.makeexpanded();
			this.partner.autoexpandstate = 'seton';
		}
	}
	else // if (this.autoexpandstate == 'seton')
	{
		this.autoexpandstate = 'mouse';
		this.makecontracted();
		if (this.partner)
		{
			this.partner.makecontracted();
			this.partner.autoexpandstate = 'mouse';
		}
	}	
}

