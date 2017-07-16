import time
from selenium import webdriver
from bs4 import BeautifulSoup
import requests

PATH = "/Users/kennyjacoby/Documents/scrapers/inspections/"
MASTER = open(PATH + "MASTER.txt", "w")

class ScrapingBrowser(webdriver.Chrome):
	def __init__(self, addr, *args, **kwargs):
		super(ScrapingBrowser, self).__init__(*args, **kwargs)
		self.implicitly_wait(6)
		self.get(addr)

	def click_xpath(self, location):
		self.find_element_by_xpath(location).click()

def getFacilities(browser, city):
	total = 0
	f = open(PATH + "{}.txt".format(city.lower()), "w")
	f.write('Name|Address|Last Inspection|Score|Grade|Inspection Date|Inspection Type|Result|Major Violations|Minor Violations|City|URL\n')
	f.close()
	soup = BeautifulSoup(browser.page_source, "html.parser")
	form = soup.find("form")
	if form['action'] != 'NoResults.aspx':
		pages = int(soup.find("span", {"id":"lblTotPages"}).font.contents[0])
		if (soup.find("a", {"id":"Linkbutton3"}) is not None):
			browser.click_xpath('//*[@id="Linkbutton3"]')
			time.sleep(1)
			soup = BeautifulSoup(browser.page_source, "html.parser")
		rows = soup.find("table", {"id":"dgSearchResults"}).tbody.findAll("tr")
		#for i in range(len(rows)):
		for i in range(5613, 18281):
			if (i % 3 == 0):
				link = 'http://www2.sdcounty.ca.gov/ffis/' + str(rows[i].td.font.a['href'])
				total += getData(link, city, total)
	print("\n{}: {} inspections".format(city, total))
	return total

def getResults(url, start_time):
	total = 0
	for i in range(41, 42):
		browser = ScrapingBrowser(url)
		soup = BeautifulSoup(browser.page_source, "html.parser")
		city = soup.find("select", {"id":"lbCity"}).findAll("option")[i-1].contents[0].strip().encode('utf8')
		browser.click_xpath('//*[@id="lbCity"]/option[{}]'.format(i))
		time.sleep(.2)
		browser.click_xpath('//*[@id="btSubmit"]')
		time.sleep(1)
		total += getFacilities(browser, city)
		print("{} total inspections".format(total))
		browser.close()
		print('\n{} minutes, {} seconds\n'.format(int(round((time.time() - start_time)//60)), int(round((time.time() - start_time)%60))))

def getContents(field):
	if len(field) > 0:
		field = field[0].strip().encode('utf8')
	return field

def getPageInfo(url):
	r = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data)
	if soup.find("span", {"id":"lblMessage"}) is None:
		info = soup.findAll("table")[4].findAll("tr")
		return info
	else:
		return None

def getData(url, city, ctr):
	ctr = 0
	info = getPageInfo(url)
	if info is not None:
		name = getContents(info[0].findAll("span")[-1].font.contents)
		address = getContents(info[1].findAll("span")[-1].font.contents)
		last_insp = getContents(info[2].findAll("span")[-1].font.contents)
		score = getContents(info[3].findAll("span")[-1].font.contents)
		if (score == 'Score:' or score == []):
			score = 'NULL'
		grade = getContents(info[4].findAll("span")[-1].font.contents)
		if (grade == 'Grade:' or grade == []):
			grade = 'NULL'
		rows = info[6].findAll("tr")
		for i in range(1, len(rows)):
			fields = rows[i].findAll("td")
			insp_date = fields[0].font.contents[0].encode('utf8')
			insp_type = fields[1].font.contents[0].contents[0].encode('utf8')
			result = fields[2].font
			if result.a is None:
				result = result.contents[0].encode('utf8')
			else:
				result = result.a.contents[0].encode('utf8')
			major = fields[3].font
			if major.a is None:
				major_violations = major.contents[0].encode('utf8')
			else:
				major_violations = []
				violations = major.findAll("a")
				for violation in violations:
					major_violations.append(violation.contents[0].strip().encode('utf8'))
			minor = fields[4].font
			if minor.a is None:
				minor_violations = minor.contents[0].encode('utf8')
			else:
				link = 'http://www2.sdcounty.ca.gov/ffis/' + minor.a['href']
				minor_violations = getViolations(link, i, 4)
			MASTER.write("{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(name, address, last_insp, score, grade, insp_date, insp_type, result, major_violations, minor_violations, city, url))
			f = open(PATH + "{}.txt".format(city.lower()), "a")
			f.write("{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(name, address, last_insp, score, grade, insp_date, insp_type, result, major_violations, minor_violations, city, url))
			print("{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(name, address, last_insp, score, grade, insp_date, insp_type, result, major_violations, minor_violations, city, url))
			ctr += 1
	return ctr

def getViolations(url, row, column):
	try:
		final = []
		info = getPageInfo(url)
		rows = info[6].findAll("tr")
		violations = rows[row].findAll("td")[column].font.findAll("a")
		for violation in violations:
			final.append(violation.contents[0].strip().encode('utf8'))
		return final
	except:
		print(url)

def main():
	start_time = time.time()
	url = 'http://www2.sdcounty.ca.gov/ffis/'
	MASTER.write('Name|Address|Last Inspection|Score|Grade|Inspection Date|Inspection Type|Result|Major Violations|Minor Violations|City|URL\n')
	getResults(url, start_time)
	print('\n{} minutes, {} seconds'.format(int(round((time.time() - start_time)//60)), int(round((time.time() - start_time)%60))))

if __name__ == "__main__":
    main()