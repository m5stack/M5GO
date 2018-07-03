from m5stack import lcd, node_id
import network, ubinascii, machine
import ujson as json
import utime as time
import usocket as socket

wlan_sta = network.WLAN(network.STA_IF); 
wlan_ap = network.WLAN(network.AP_IF)
scanlist = []

def do_connect(ntwrk_ssid, netwrk_pass):
	if not wlan_sta.isconnected():
		print('M5Stack Core try to connect WiFi: SSID:'+ntwrk_ssid+' PASSWD:'+netwrk_pass+' network...')
		# lcd.println('M5Stack Core try to connect WiFi: \r\nWiFi SSID:'+ntwrk_ssid+' \t\nPASSWD:'+netwrk_pass)
		wlan_sta.active(True)
		wlan_sta.connect(ntwrk_ssid, netwrk_pass)
		# lcd.print('Connecting.')
		a = 0
		while not wlan_sta.isconnected() | (a > 100) :
			time.sleep(0.2)
			a += 1
			print('.', end='')
			# lcd.print('.')
		if wlan_sta.isconnected():
			print('\nConnected. Network config:', wlan_sta.ifconfig())
			# lcd.println("Connected! \r\nNetwork config:\r\n"+wlan_sta.ifconfig()[0]+', '+wlan_sta.ifconfig()[3])
			return (True)
		else : 
			print('\nProblem. Not Connected to :'+ntwrk_ssid)
			# lcd.println('Problem. Not Connected to :'+ntwrk_ssid)
			return (False)


def save_wifi(ssid, password):
	try:
		wifidata = {}
		wifidata['ssid'] = ssid
		wifidata['password'] = password
		with open("wificonfig.json", "r") as fo:
			cfg = fo.read()
		with open("wificonfig.json", "w") as fo:
			cfg = json.loads(cfg)
			cfg['wifi'] = wifidata
			fo.write(json.dumps(cfg))
	except:
		with open("wificonfig.json", "w") as fo:
			cfg = {}
			cfg['wifi'] = wifidata
			fo.write(json.dumps(cfg))

first_scan = True
def _httpHanderRoot(httpClient, httpResponse):
	global scanlist, first_scan
	response_header = """\
<html><meta name="viewport" content="width=device-width,height=device-height,initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>input,button{appearance:none;-moz-appearance:none;-webkit-appearance:none}p{margin:10px 0}h1,h2{text-align:center;margin:35px 0}h2{margin:20px 0!important}form{margin-top:30px}tr td{text-align:right}tr select,tr input[type=password],tr input[type=text]{width:200px;height:30px;padding-left:10px;outline:0;border-radius:3px;border:1px solid lightgrey}tr input[type=checkbox]{width:18px;height:18px;appearance:checkbox;-webkit-appearance:checkbox;-moz-appearance:checkbox;}input[type="submit"]{width:300px;height:38px;color:#fff;background-color:#2196f1;border:0;font-size:20px;border-radius:3px;margin-top:20px}#mask{position:absolute;top:0;left:0;right:0;bottom:0;width:100%;height:100%;background-color:rgba(255,255,255,0.9);display:none}.wrap{position:absolute;top:0;left:0;right:0;bottom:0;margin:120px auto;width:280px}h4{font-size:22px;text-align:center}.progress-bar-wrap{width:280px;height:20px;border-radius:6px;overflow:hidden}</style>
<h1>M5GO</h1>
<h2 style="color: #333"><p style="font-weight:100;font-size:32px;">WiFi Setup</p></h2>
<form name="form" action="configure" method="get"><table style="margin-left: auto; margin-right: auto;"><tbody><tr><td>SSID:</td><td id="td_ssid" style="text-align: center;">
<select id="ssid" name="ssid">
"""

	response_variable = ""
	if first_scan:
		first_scan = False
		for ssid, *_ in scanlist:
			response_variable += '<option value="{0}">{0}</option>'.format(ssid.decode("utf-8"))
	else:
		for ssid, *_ in wlan_sta.scan():
			response_variable += '<option value="{0}">{0}</option>'.format(ssid.decode("utf-8"))

	response_footer = """\
</select>
</td><td><input name="other" type="checkbox" onchange="toggleSSIDInput(this.checked)"><span>Other</span></td></tr><tr><td>Password:</td><td><input name="password" type="password">
</td></tr></tbody></table><p style="text-align: center;"><input type="submit" value="Configure" onclick="showLoading()"></p></form>
<div id="mask"><div class="wrap"><h4 id="info_text">Connecting Wifi ...</h4></div></div>
<script>function showLoading() { document.getElementById("mask").style.display = "block" };</script>
<script>var bakELe=null;var el_ssid_input=document.createElement("input");el_ssid_input.id="ssid_input";el_ssid_input.name="ssid";el_ssid_input.type="text";function toggleSSIDInput(flag){var td_ssid=document.getElementById("td_ssid");var ssid=document.getElementById("ssid");var ssid_input=document.getElementById("ssid_input");if(flag){bakELe=ssid.cloneNode(true);td_ssid.appendChild(el_ssid_input);td_ssid.removeChild(ssid);document.forms[0]["other"].value="true"}else{td_ssid.appendChild(bakELe);bakELe=ssid_input.cloneNode(true);td_ssid.removeChild(ssid_input);document.forms[0]["other"].value="false"}};</script></html>
"""

	content = response_header + response_variable + response_footer
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	   = "text/html",
								  contentCharset = "UTF-8",
								  content 		   = content )


def _httpHanderConfig(httpClient, httpResponse) :
	formData  = httpClient.GetRequestQueryParams()
	ssid      = formData.get("ssid")
	password  = formData.get("password")
	other_flg = formData.get("other")
	print(formData)
	content = ''
	is_connected = False

	if other_flg == 'true' or do_connect(ssid, password):
		is_connected = True
		save_wifi(ssid, password)
		content = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta http-equiv="X-UA-Compatible" content="ie=edge"><style>h1{text-align:center;margin-top:120px;font-size:1.4rem;color:#0064a0}p{text-align:center;font-size:1.1rem}div{width:200px;margin:0 auto;padding-left:60px}</style><title></title></head><body><h1>^_^ WiFi connection success</h1><div><span>Reset device now </span><span id="wating">...</span></div></body><script>var wating=document.getElementById("wating");setInterval(function(){if(wating.innerText==="..."){return wating.innerText="."}wating.innerText+="."},500);</script></html>"""
	else:
		content = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta http-equiv="X-UA-Compatible" content="ie=edge"><style>h1{text-align:center;margin-top:120px;font-size:1.4rem;color:red}p{text-align:center;font-size:1.1rem}</style><title></title></head><body><h1>×_× WiFi connection failed</h1><p>Click <a href="/">here</a> return configure page.</p></body></html>"""

	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )

	if is_connected:
		time.sleep(3)
		wlan_ap.active(False)
		machine.reset()


routeHandlers = [
	( "/",	        "GET",	_httpHanderRoot ),
	( "/wifi",	    "GET",	_httpHanderRoot ),
	( "/configure",	"GET",	_httpHanderConfig )
]

def webserver_start():
	global scanlist
	# wlan_ap.eventCB(wlan_ap_cb)
	wlan_ap.active(True)
	# node_id = ubinascii.hexlify(machine.unique_id())
	ssid_name= "M5GO-"+node_id[-4:]
	# lcd.font(lcd.FONT_Comic, transparent=True)
	# lcd.print(ssid_name, 135, 190, lcd.RED)
	wlan_ap.config(essid=ssid_name, authmode=network.AUTH_OPEN)
	addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
	print('WiFi AP WebServer Start!')
	print('Connect to Wifi ssid:'+ssid_name)
	print('And connect to esp via your web browser (like 192.168.4.1)')
	print('listening on', addr)
	# lcd.println(b'Connect to Wifi ssid:'+ssid_name)
	# lcd.println('via your web browser: 192.168.4.1')
	# lcd.println('listening on'+str(addr))
	scanlist = wlan_sta.scan()
	from microWebSrv import MicroWebSrv
	webserver = MicroWebSrv(routeHandlers=routeHandlers)
	webserver.Start(threaded=False)
